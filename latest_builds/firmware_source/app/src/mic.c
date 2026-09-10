#include <errno.h>
#include <string.h>

#include <haly/nrfy_gpio.h>
#include <zephyr/irq.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>

#include "config.h"
#include "mic.h"
#include "e1_board.h"
#include "nrfx_clock.h"
#include <zephyr/drivers/clock_control/nrf_clock_control.h>
#include <zephyr/sys/onoff.h>
#include "nrfx_pdm.h"

LOG_MODULE_REGISTER(mic, CONFIG_LOG_DEFAULT_LEVEL);

#define PDM_STOP_TIMEOUT_MS 250

static int16_t buffer_0[MIC_BUFFER_SAMPLES];
static int16_t buffer_1[MIC_BUFFER_SAMPLES];
static atomic_t next_buffer_index;
static atomic_t warmup_blocks;
static mic_handler sample_callback;
static mic_error_handler error_callback;
static atomic_t initialized;
static atomic_t running;
static atomic_t hardware_started;
static atomic_t stopping;
static atomic_t session_epoch;
static K_MUTEX_DEFINE(mic_lifecycle_lock);
static struct onoff_manager *hf_manager;
static struct onoff_client hf_client;
static bool hf_owned;
static int clock_acquire(void)
{
 if(hf_owned) return 0;
 sys_notify_init_spinwait(&hf_client.notify);
 int err=onoff_request(hf_manager,&hf_client);
 if(err<0) return err;
 int result; int64_t deadline=k_uptime_get()+250;
 while(sys_notify_fetch_result(&hf_client.notify,&result)==-EAGAIN) {
  if(k_uptime_get()>deadline) { (void)onoff_cancel_or_release(hf_manager,&hf_client); return -ETIMEDOUT; }
  k_msleep(1);
 }
 if(result<0) return result;
 hf_owned=true; return 0;
}
static void clock_release(void)
{
 if(hf_owned) { (void)onoff_release(hf_manager); hf_owned=false; }
}

K_SEM_DEFINE(pdm_stopped, 0, 1);

static int stop_hardware_locked(void)
{
    atomic_clear(&running);
    int power_error = e1_mic_power(false);
    if (!atomic_get(&hardware_started)) {
        memset(buffer_0, 0, sizeof(buffer_0));
        memset(buffer_1, 0, sizeof(buffer_1));
        return power_error;
    }
    if (atomic_get(&stopping)) {
        int wait_error =
            k_sem_take(&pdm_stopped, K_MSEC(PDM_STOP_TIMEOUT_MS));
        if (wait_error != 0) {
            LOG_ERR("PDM remains in the stopping state: %d",
                    wait_error);
            return -ETIMEDOUT;
        }
        memset(buffer_0, 0, sizeof(buffer_0));
        memset(buffer_1, 0, sizeof(buffer_1));
        return power_error;
    }

    k_sem_reset(&pdm_stopped);
    atomic_set(&stopping, 1);
    nrfx_err_t result = nrfx_pdm_stop();
    if (result != NRFX_SUCCESS) {
        atomic_clear(&stopping);
        LOG_ERR("PDM stop failed: %d", result);
        return -EIO;
    }

    /*
     * Pinned nrfx stops STARTING/IDLE synchronously, but RUNNING stops only
     * after the current frame and a final callback. Never scrub DMA buffers
     * or permit restart until the peripheral is observably disabled.
     */
    if (nrfx_pdm_enable_check()) {
        int wait_error =
            k_sem_take(&pdm_stopped, K_MSEC(PDM_STOP_TIMEOUT_MS));
        if (wait_error != 0) {
            LOG_ERR("Timed out waiting for PDM quiescence: %d",
                    wait_error);
            return -ETIMEDOUT;
        }
    } else {
        atomic_clear(&hardware_started);
        atomic_clear(&stopping);
    }

    memset(buffer_0, 0, sizeof(buffer_0));
    memset(buffer_1, 0, sizeof(buffer_1));
    return power_error;
}

static void record_pdm_fault(int error)
{
    if (error == 0) {
        error = -EIO;
    }
    atomic_val_t fault_epoch = atomic_get(&session_epoch);
    if (!atomic_cas(&running, 1, 0)) {
        return;
    }
    if (fault_epoch != atomic_get(&session_epoch)) {
        return;
    }
    e1_mic_power_off_async();
    /*
     * The registered callback is transport_audio_fault(), which only uses
     * ISR-safe atomics, a spinlock, and k_sem_give(). The audio-control
     * thread owns the serialized/quiescence-confirmed nrfx stop.
     */
    if (error_callback != NULL) {
        error_callback(error);
    }
}

static void pdm_irq_handler(nrfx_pdm_evt_t const *event)
{
    if (atomic_get(&stopping)) {
        if (!nrfx_pdm_enable_check()) {
            atomic_clear(&hardware_started);
            atomic_clear(&stopping);
            k_sem_give(&pdm_stopped);
        }
        return;
    }

    if (event->error != 0) {
        LOG_ERR("PDM IRQ error: %d", event->error);
        record_pdm_fault(-EIO);
        return;
    }

    if (event->buffer_requested && atomic_get(&running)) {
        atomic_val_t buffer_index = atomic_inc(&next_buffer_index);
        int16_t *next_buffer =
            (buffer_index & 1) == 0 ? buffer_0 : buffer_1;
        nrfx_err_t result =
            nrfx_pdm_buffer_set(next_buffer, MIC_BUFFER_SAMPLES);
        if (result != NRFX_SUCCESS) {
            LOG_ERR("PDM buffer queue failed: %d", result);
            record_pdm_fault(-ENOBUFS);
            return;
        }
    }

    if (event->buffer_released != NULL && atomic_get(&running) &&
        sample_callback != NULL) {
        if(!atomic_cas(&warmup_blocks,1,0)) sample_callback(event->buffer_released);
    }
}

int mic_init(void)
{
    if (atomic_get(&initialized)) {
        return 0;
    }

    hf_manager=z_nrf_clock_control_get_onoff(CLOCK_CONTROL_NRF_SUBSYS_HF);
    if(!hf_manager) return -ENODEV;

    nrfx_pdm_config_t config =
        NRFX_PDM_DEFAULT_CONFIG(PDM_CLK_PIN, PDM_DIN_PIN);
    config.gain_l = MIC_GAIN;
    config.gain_r = MIC_GAIN;
    config.interrupt_priority = MIC_IRC_PRIORITY;
    config.clock_freq = NRF_PDM_FREQ_1280K;
    config.mode = NRF_PDM_MODE_MONO;
    config.edge = NRF_PDM_EDGE_LEFTFALLING;
    config.ratio = NRF_PDM_RATIO_80X;

    /*
     * Match the pinned Zephyr nrfx PDM driver: nrfx_isr is a regular,
     * kernel-aware ISR wrapper. The event callback may therefore use
     * ISR-safe Zephyr primitives such as k_sem_give().
     */
    IRQ_CONNECT(
        PDM_IRQn, MIC_IRC_PRIORITY,
        nrfx_isr, nrfx_pdm_irq_handler, 0);
    nrfx_err_t result = nrfx_pdm_init(&config, pdm_irq_handler);
    if (result != NRFX_SUCCESS) {
        LOG_ERR("PDM initialization failed: %d", result);
        return -EIO;
    }

    int power_error = e1_mic_power(false);
    if (power_error) { return power_error; }
    atomic_set(&initialized, 1);
    return 0;
}

int mic_start(void)
{
    k_mutex_lock(&mic_lifecycle_lock, K_FOREVER);
    if (!atomic_get(&initialized)) {
        k_mutex_unlock(&mic_lifecycle_lock);
        return -EACCES;
    }
    if (atomic_get(&running)) {
        k_mutex_unlock(&mic_lifecycle_lock);
        return 0;
    }
    if (atomic_get(&hardware_started) ||
        atomic_get(&stopping)) {
        k_mutex_unlock(&mic_lifecycle_lock);
        return -EBUSY;
    }

    atomic_inc(&session_epoch);
    atomic_set(&next_buffer_index, 0);
    atomic_set(&warmup_blocks,1);
    memset(buffer_0, 0, sizeof(buffer_0));
    memset(buffer_1, 0, sizeof(buffer_1));
    int clock_error=clock_acquire();
    if(clock_error) { k_mutex_unlock(&mic_lifecycle_lock); return clock_error; }
    int power_error = e1_mic_power(true);
    if (power_error) { clock_release(); k_mutex_unlock(&mic_lifecycle_lock); return power_error; }
    atomic_set(&hardware_started, 1);
    atomic_set(&running, 1);
    nrfx_err_t result = nrfx_pdm_start();
    if (result != NRFX_SUCCESS) {
        atomic_clear(&running);
        atomic_clear(&hardware_started);
        atomic_inc(&session_epoch);
        e1_mic_power_off_async();
        clock_release();
        LOG_ERR("PDM start failed: %d", result);
        k_mutex_unlock(&mic_lifecycle_lock);
        return -EIO;
    }
    k_mutex_unlock(&mic_lifecycle_lock);
    return 0;
}

int mic_stop(void)
{
    k_mutex_lock(&mic_lifecycle_lock, K_FOREVER);
    /*
     * Clear running before advancing the epoch so an IRQ can only claim the
     * old session or observe a stopped microphone, never the new epoch.
     */
    atomic_clear(&running);
    atomic_inc(&session_epoch);
    int err = stop_hardware_locked();
    if(!atomic_get(&hardware_started)) clock_release();
    k_mutex_unlock(&mic_lifecycle_lock);
    return err;
}

bool mic_is_running(void)
{
    return atomic_get(&running) != 0;
}

void mic_emergency_power_off(void)
{
    atomic_clear(&running);
    atomic_inc(&session_epoch);
    nrf_pdm_disable(NRF_PDM);
    e1_mic_power_off_async();
}

void set_mic_callback(mic_handler callback)
{
    sample_callback = callback;
}

void set_mic_error_callback(mic_error_handler callback)
{
    error_callback = callback;
}
