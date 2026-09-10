/* Anticipy E1 bring-up adapter. Register definitions follow NCS 2.7.0
 * Zephyr nPM1300 drivers; TDK curve 8307 replaces the driver's beta estimate.
 * This image does not enable charging or write/erase the NAND. */
#include <errno.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/mfd/npm1300.h>
#include <zephyr/logging/log.h>
#include "e1_board.h"
LOG_MODULE_REGISTER(e1_board, LOG_LEVEL_INF);
static const struct device *const pmic = DEVICE_DT_GET(DT_NODELABEL(e1_pmic));
static const struct device *const charger = DEVICE_DT_GET(DT_NODELABEL(e1_charger));
static const struct spi_dt_spec nand = SPI_DT_SPEC_GET(DT_NODELABEL(nand), SPI_WORD_SET(8) | SPI_TRANSFER_MSB, 0);
static K_MUTEX_DEFINE(power_lock);
static bool ready;
static struct k_work mic_off_work;
static struct k_work_sync mic_off_sync;
static int write_checked(uint8_t base, uint8_t offset, uint8_t value)
{
 uint8_t got; int err = mfd_npm1300_reg_write(pmic,base,offset,value);
 if (err) return err;
 err = mfd_npm1300_reg_read(pmic,base,offset,&got);
 return err ? err : got == value ? 0 : -EIO;
}
int e1_charge_disable(void) { return mfd_npm1300_reg_write(pmic,0x03,0x05,1); }
int e1_mic_power(bool on)
{
 if (k_is_in_isr()) return -EWOULDBLOCK;
 if(on) k_work_cancel_sync(&mic_off_work,&mic_off_sync);
 k_mutex_lock(&power_lock,K_FOREVER);
 int err = ready ? mfd_npm1300_reg_write(pmic,0x08,on ? 0x00 : 0x01,1) : -ENODEV;

 k_mutex_unlock(&power_lock);
 return err;
}
static void power_off_work(struct k_work *work)
{
 ARG_UNUSED(work);
 int err=e1_mic_power(false);
 if(err) LOG_ERR("Microphone power off failed: %d",err);
}

void e1_mic_power_off_async(void) { k_work_submit(&mic_off_work); }
int e1_battery_mv(uint16_t *mv)
{
 if (!mv) return -EINVAL;
 struct sensor_value value;
 k_mutex_lock(&power_lock,K_FOREVER);
 int err=sensor_sample_fetch(charger);
 if(!err) { k_msleep(5); err=sensor_sample_fetch(charger); }
 if(!err) err=sensor_channel_get(charger,SENSOR_CHAN_GAUGE_VOLTAGE,&value);
 k_mutex_unlock(&power_lock);
 if(err) return err;
 int64_t millivolts=(int64_t)value.val1*1000+value.val2/1000;
 if(millivolts<0 || millivolts>5500) return -ERANGE;
 *mv=(uint16_t)millivolts; return 0;
}
int e1_ntc_millicelsius(int32_t *out)
{
 /* TDK B57540G1103F000, curve 8307. Linear interpolation over 5 C
  * intervals is a prototype estimate, not a calibrated cell measurement. */
 static const uint32_t resistance[]={280240,225200,182160,148270,121420,100000,82818,68954,57703,48525,41000,34798,29663};
 if(!out) return -EINVAL;
 uint8_t data[6]; int err;
 k_mutex_lock(&power_lock,K_FOREVER);
 err=mfd_npm1300_reg_write(pmic,0x05,0x01,1);
 if(!err) { k_msleep(5); err=mfd_npm1300_reg_read_burst(pmic,0x05,0x10,data,sizeof(data)); }
 k_mutex_unlock(&power_lock);
 if(err) return err;
 unsigned code=((unsigned)data[2]<<2)|((data[5]>>2)&3u);
 if(code==0 || code>=1023) return -ENODATA;
 uint32_t r10=(100000u*code)/(1024u-code);
 if(r10>resistance[0] || r10<resistance[12]) return -ERANGE;
 for(unsigned i=0;i<12;i++) if(r10<=resistance[i] && r10>=resistance[i+1]) {
  *out=(int32_t)(i*5000u + ((resistance[i]-r10)*5000u)/(resistance[i]-resistance[i+1])); return 0;
 }
 return -ERANGE;
}
int e1_nand_probe(uint8_t id[2])
{
 if(!id || !spi_is_ready_dt(&nand)) return -ENODEV;
 /* 9Fh, one dummy address byte, then manufacturer and device IDs. */
 uint8_t tx[4]={0x9f,0,0,0},rx[4]={0};
 struct spi_buf tb={.buf=tx,.len=sizeof(tx)},rb={.buf=rx,.len=sizeof(rx)};
 struct spi_buf_set ts={.buffers=&tb,.count=1},rs={.buffers=&rb,.count=1};
 int err=spi_transceive_dt(&nand,&ts,&rs);
 if(err) return err;
 id[0]=rx[2];id[1]=rx[3];
 return (id[0]==0xc2 && id[1]==0x37) ? 0 : -ENODEV;
}
int e1_board_init(void)
{
 if(!device_is_ready(pmic)||!device_is_ready(charger)) return -ENODEV;
 int err=e1_charge_disable();
 if(err) return err;
 /* LDSW1 drives 3V_MIC; LDSW2 is unused. Both off before advertising. */
 if((err=mfd_npm1300_reg_write(pmic,0x08,0x01,1))) return err;
 if((err=mfd_npm1300_reg_write(pmic,0x08,0x03,1))) return err;
 if((err=write_checked(0x08,0x08,0))) return err;
 /* NTC comparator codes for 5 C cold, 10 C cool, 40 C warm/hot.
  * Deliberately narrower than the LP571225 0..45 C charging range.
  * Charging remains disabled until physical tolerance/fault qualification. */
 const uint16_t code[4]={709,661,375,375};
 for(unsigned i=0;i<4;i++) {
  if((err=write_checked(0x03,0x10+i*2,code[i]>>2))) return err;
  if((err=write_checked(0x03,0x11+i*2,code[i]&3))) return err;
 }
 const struct device *gpio0=DEVICE_DT_GET(DT_NODELABEL(gpio0));
 const struct device *gpio1=DEVICE_DT_GET(DT_NODELABEL(gpio1));
 /* NAND WP/IO2 and HOLD/IO3 stay high in single-SPI bring-up. */
 if((err=gpio_pin_configure(gpio0,23,GPIO_OUTPUT_HIGH))) return err;
 if((err=gpio_pin_configure(gpio1,0,GPIO_OUTPUT_HIGH))) return err;
 if((err=gpio_pin_configure(gpio0,8,GPIO_OUTPUT_LOW))) return err;
 k_work_init(&mic_off_work,power_off_work);
 ready=true;
 uint8_t id[2];err=e1_nand_probe(id);
 if(err) LOG_WRN("NAND identification unavailable: %d",err);
 else LOG_INF("NAND ID %02x %02x; no data written",id[0],id[1]);
 LOG_INF("E1P1 BUCK2 main; BUCK1/TP12 off after init; charging disabled");
 return 0;
}
