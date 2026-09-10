#include <errno.h>
#include <zephyr/device.h>
#include <zephyr/drivers/led.h>
#include "led.h"
static const struct device *const leds=DEVICE_DT_GET(DT_NODELABEL(e1_leds));
int led_start(void) {
 if(!device_is_ready(leds)) return -ENODEV;
 int err=led_off(leds,0); return err ? err : led_off(leds,1);
}
int set_led_blue(bool on) { return on ? led_on(leds,0) : led_off(leds,0); }
int set_led_red(bool on) { return on ? led_on(leds,1) : led_off(leds,1); }

/* A visible 2 Hz red recording pulse, 100 ms on / 400 ms off. At the
 * nPM1300's nominal 5 mA LED sink this averages 1 mA. Red also has more
 * forward-voltage margin than blue near an empty cell. Optical visibility
 * and actual current remain first-article measurements. */
#include <zephyr/kernel.h>
#include "transport.h"
static K_MUTEX_DEFINE(indicator_lock);
static bool recording_active;
static bool recording_lit;
static void indicator_tick(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(recording_work,indicator_tick);
static struct k_work_sync recording_sync;
static void indicator_tick(struct k_work *work)
{
 ARG_UNUSED(work);
 int err=0;
 k_mutex_lock(&indicator_lock,K_FOREVER);
 if(recording_active) {
  recording_lit=!recording_lit;
  err=set_led_red(recording_lit);
  if(err) recording_active=false;
  else k_work_reschedule(&recording_work,K_MSEC(recording_lit ? 100 : 400));
 }
 k_mutex_unlock(&indicator_lock);
 if(err) transport_audio_fault(err);
}
int recording_indicator_stop(void)
{
 k_mutex_lock(&indicator_lock,K_FOREVER);recording_active=false;k_mutex_unlock(&indicator_lock);
 k_work_cancel_delayable_sync(&recording_work,&recording_sync);
 k_mutex_lock(&indicator_lock,K_FOREVER);
 int err=set_led_red(false);recording_lit=false;
 k_mutex_unlock(&indicator_lock);
 return err;
}
int recording_indicator_start(void)
{
 int err=recording_indicator_stop();if(err)return err;
 k_mutex_lock(&indicator_lock,K_FOREVER);
 err=set_led_red(true);
 if(!err) {recording_active=true;recording_lit=true;k_work_reschedule(&recording_work,K_MSEC(100));}
 k_mutex_unlock(&indicator_lock);
 return err;
}
