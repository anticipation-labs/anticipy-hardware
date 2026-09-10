#include <stdbool.h>
#include <stdint.h>
#include <errno.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "codec.h"
#include "config.h"
#include "led.h"
#include "mic.h"
#include "e1_board.h"
#include "transport.h"
#include "watchdog.h"

#define BOOT_BLINK_DURATION_MS 600
#define BOOT_PAUSE_DURATION_MS 200

LOG_MODULE_REGISTER(main, CONFIG_LOG_DEFAULT_LEVEL);

/*
 * A FULL RING IS THE RADIO BEING BEHIND, NOT THE STREAM BEING OVER.
 *
 * Both handlers below used to hand every non-zero result to
 * transport_audio_fault, and that call switches the microphone off for the
 * remainder of the connection — recoverable only by a fresh CCC write, which
 * the phone does not send while a link is up. So a TX ring that filled for
 * 320ms, or a PCM ring that filled for a second, ended capture for the whole
 * session. Both rings drain on their own; neither says the stream is invalid.
 *
 * Dropping the block instead loses a tenth of a second of audio and keeps the
 * microphone alive, which is the trade Omi makes in the same place. There is
 * deliberately no counter here: the transport owns the loss count, because a
 * number kept in two places is a number that disagrees with itself.
 */
static void codec_handler(uint8_t *data, size_t len)
{
    if (!transport_audio_is_active()) {
        return;
    }

    int err = broadcast_audio_packets(data, len);
    if (err == -ENOSPC) {
        LOG_WRN("TX ring full, dropping one audio frame");
        return;
    }
    if (err != 0 && err != -ECANCELED) {
        LOG_ERR("Failed to queue audio packet: %d", err);
        transport_audio_fault(err);
    }
}

static void handle_mic_samples(int16_t *buffer)
{
    if (!transport_audio_is_active()) {
        return;
    }

    int err = codec_receive_pcm(buffer, MIC_BUFFER_SAMPLES);
    if (err == -ENOSPC) {
        LOG_WRN("PCM ring full, dropping one microphone block");
        return;
    }
    if (err != 0 && err != -ECANCELED) {
        LOG_ERR("Failed to queue PCM data: %d", err);
        transport_audio_fault(err);
    }
}

static void handle_mic_error(int error)
{
    transport_audio_fault(error);
}

void bt_ctlr_assert_handle(char *name, int type)
{
    /*
     * Controller state is no longer trustworthy. Cut microphone power
     * directly, leave the recording indicator conservatively lit, and enter
     * Zephyr's fatal path instead of returning to corrupt streaming state.
     */
    mic_emergency_power_off();
    /* Do not issue I2C transactions from the controller fatal ISR. */
    LOG_ERR("Bluetooth controller assertion: %s (type %d)",
            name ? name : "NULL", type);
    k_panic();
}

static int boot_led_sequence(void)
{
 int err=set_led_red(true); if(err)return err; k_msleep(150);
 err=set_led_red(false); if(err)return err;
 err=set_led_blue(true); if(err)return err; k_msleep(150);
 return set_led_blue(false);
}

static void show_startup_failure(void)
{
    for (int index = 0; index < 5; index++) {
        set_led_red(true);
        k_msleep(200);
        set_led_red(false);
        k_msleep(200);
    }
}

int main(void)
{
    /* This custom-board image is programmed and recovered over SWD. */
    int err=e1_board_init();
    if(err) { LOG_ERR("E1 power initialization failed: %d",err); return err; }

    err = led_start();
    if (err != 0) {
        /*
         * The LEDs are the physical recording indicator. Refuse to
         * initialize the microphone or advertise when they are unavailable.
         * SWD remains the recovery interface if startup fails.
         */
        LOG_ERR("Recording indicator unavailable: %d", err);
        return err;
    }
    err = boot_led_sequence();
    if (err != 0) {
        LOG_ERR("Recording indicator self-test failed: %d", err);
        return err;
    }

    set_codec_callback(codec_handler);
    set_codec_error_callback(handle_mic_error);
    err = codec_start();
    if (err != 0) {
        LOG_ERR("Failed to initialize codec: %d", err);
        show_startup_failure();
        return err;
    }

    set_mic_callback(handle_mic_samples);
    set_mic_error_callback(handle_mic_error);
    err = mic_init();
    if (err != 0) {
        LOG_ERR("Failed to initialize microphone: %d", err);
        show_startup_failure();
        return err;
    }

    /*
     * Advertising is the startup commit. The codec, microphone, and physical
     * indicator are ready before an iPhone can discover codec ID 20.
     */
    err = transport_start();
    if (err != 0) {
        LOG_ERR("Failed to start transport: %d", err);
        show_startup_failure();
        return err;
    }

    /* Arm after successful startup so initialization failures remain on SWD
     * without repeated boot loops. A watchdog failure is logged, non-fatal. */
    int watchdog_error = watchdog_start();
    if (watchdog_error != 0) {
        LOG_WRN("Watchdog unavailable; hang recovery disabled: %d",
                watchdog_error);
    }

    LOG_INF("Anticipy live-stream firmware initialized");
    while (true) {
        watchdog_feed();
        k_sleep(K_MSEC(WATCHDOG_FEED_INTERVAL_MS));
    }
}
