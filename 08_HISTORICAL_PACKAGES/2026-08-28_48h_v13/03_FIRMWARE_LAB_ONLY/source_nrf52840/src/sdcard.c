#include "sdcard.h"

#include <errno.h>
#include <ff.h>
#include <stdio.h>
#include <string.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/fs/fs.h>
#include <zephyr/fs/fs_sys.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/pm/device.h>
#include <zephyr/storage/disk_access.h>
#include <zephyr/sys/check.h>

LOG_MODULE_REGISTER(sdcard, CONFIG_LOG_DEFAULT_LEVEL);

static FATFS fat_fs;

static struct fs_mount_t mount_point = {
    .type = FS_FATFS,
    .fs_data = &fat_fs,
};

uint8_t file_count = 0;

#define MAX_PATH_LENGTH 32
static char current_full_path[MAX_PATH_LENGTH];
static char read_buffer[MAX_PATH_LENGTH];
static char write_buffer[MAX_PATH_LENGTH];

#define SD_AUDIO_BLOCK_BYTES 440U
#define SD_AUDIO_BATCH_BLOCKS 16U
#define SD_AUDIO_BATCH_BYTES (SD_AUDIO_BLOCK_BYTES * SD_AUDIO_BATCH_BLOCKS)

static struct fs_file_t append_file;
static bool append_file_initialized;
static bool append_file_open;
static uint8_t append_cache[SD_AUDIO_BATCH_BYTES];
static size_t append_cache_length;
K_MUTEX_DEFINE(append_mutex);

static int flush_audio_file_unlocked(bool close_file);

uint32_t file_num_array[2];

static const char *disk_mount_pt = "/SD:/";

bool sd_enabled = false;
static bool sd_mounted = false;

int mount_sd_card(void)
{
    sd_mounted = false;
    /* Adafruit 5683 BFF has no SD power-enable GPIO. */
    sd_enabled = true;

    // initialize the sd card
    const char *disk_pdrv = "SD";
    int err = disk_access_init(disk_pdrv);
    LOG_INF("disk_access_init: %d\n", err);
    if (err) { // reattempt
        k_msleep(1000);
        err = disk_access_init(disk_pdrv);
        if (err) {
            LOG_ERR("disk_access_init failed");
            return -1;
        }
    }

    mount_point.mnt_point = "/SD:";
    int res = fs_mount(&mount_point);
    if (res == FR_OK) {
        LOG_INF("SD card mounted successfully");
    } else {
        LOG_ERR("f_mount failed: %d", res);
        return -1;
    }

    res = fs_mkdir("/SD:/audio");

    if (res == FR_OK) {
        LOG_INF("audio directory created successfully");
    } else if (res == FR_EXIST) {
        LOG_INF("audio directory already exists");
    } else {
        LOG_ERR("audio directory creation failed: %d", res);
        return -1;
    }

    /* The legacy phone protocol consumes one append-only file. */
    err = initialize_audio_file(1);
    if (err) {
        LOG_ERR("failed to create or open audio file: %d", err);
        return -1;
    }
    file_count = 1;
    LOG_INF("new num files: %d", file_count);

    res = move_write_pointer(file_count);
    if (res) {
        LOG_ERR("error while moving the write pointer");
        return -1;
    }

    res = move_read_pointer(file_count);
    if (res) {
        LOG_ERR("error while moving the reader pointer\n");
        return -1;
    }
    LOG_INF("file count: %d", file_count);

    struct fs_dirent info_file_entry; // check if the info file exists. if not, generate new info file
    const char *info_path = "/SD:/info.txt";
    res = fs_stat(info_path, &info_file_entry); // for later
    if (res) {
        res = create_file("info.txt");
        if (res) {
            LOG_ERR("info.txt creation failed: %d", res);
            return -1;
        }
        res = save_offset(0);
        if (res) {
            return -1;
        }
        LOG_INF("result of info.txt creation: %d ", res);
    }

    uint32_t file_size = get_file_size(1);
    int stored_offset = get_offset();
    if (stored_offset < 0 || (uint32_t) stored_offset > file_size) {
        LOG_WRN("invalid saved offset; resetting to zero");
        stored_offset = 0;
        if (save_offset(0)) {
            return -1;
        }
    }
    file_num_array[0] = file_size;
    file_num_array[1] = (uint32_t) stored_offset;
    sd_mounted = true;

    return 0;
}

uint32_t get_file_size(uint8_t num)
{
    if (flush_audio_file(true) < 0) {
        LOG_ERR("failed to flush audio before stat");
        return 0;
    }

    char *ptr = generate_new_audio_header(num);
    snprintf(current_full_path, sizeof(current_full_path), "%s%s", disk_mount_pt, ptr);
    k_free(ptr);
    struct fs_dirent entry;
    int res = fs_stat(current_full_path, &entry);
    if (res) {
        LOG_ERR("invalid file in get file size\n");
        return 0;
    }
    return (uint32_t) entry.size;
}

int move_read_pointer(uint8_t num)
{
    char *read_ptr = generate_new_audio_header(num);
    snprintf(read_buffer, sizeof(read_buffer), "%s%s", disk_mount_pt, read_ptr);
    k_free(read_ptr);
    struct fs_dirent entry;
    int res = fs_stat(read_buffer, &entry);
    if (res) {
        LOG_ERR("invalid file in move read ptr\n");
        return -1;
    }
    return 0;
}

int move_write_pointer(uint8_t num)
{
    int flush_rc = flush_audio_file(true);
    if (flush_rc < 0) {
        return flush_rc;
    }

    char *write_ptr = generate_new_audio_header(num);
    snprintf(write_buffer, sizeof(write_buffer), "%s%s", disk_mount_pt, write_ptr);
    k_free(write_ptr);
    struct fs_dirent entry;
    int res = fs_stat(write_buffer, &entry);
    if (res) {
        LOG_ERR("invalid file in move write pointer\n");
        return -1;
    }
    return 0;
}

int create_file(const char *file_path)
{
    int ret = 0;
    snprintf(current_full_path, sizeof(current_full_path), "%s%s", disk_mount_pt, file_path);
    struct fs_file_t data_file;
    fs_file_t_init(&data_file);
    ret = fs_open(&data_file, current_full_path, FS_O_WRITE | FS_O_CREATE);
    if (ret) {
        LOG_ERR("File creation failed %d", ret);
        return -2;
    }
    fs_close(&data_file);
    return 0;
}

int read_audio_data(uint8_t *buf, int amount, int offset)
{
    k_mutex_lock(&append_mutex, K_FOREVER);
    int flush_rc = flush_audio_file_unlocked(true);
    if (flush_rc < 0) {
        k_mutex_unlock(&append_mutex);
        return flush_rc;
    }

    struct fs_file_t read_file;
    fs_file_t_init(&read_file);
    uint8_t *temp_ptr = buf;
    int rc = fs_open(&read_file, read_buffer, FS_O_READ);
    if (rc < 0) {
        k_mutex_unlock(&append_mutex);
        return rc;
    }
    rc = fs_seek(&read_file, offset, FS_SEEK_SET);
    if (rc < 0) {
        fs_close(&read_file);
        k_mutex_unlock(&append_mutex);
        return rc;
    }
    rc = fs_read(&read_file, temp_ptr, amount);
    // LOG_PRINTK("read data :");
    // for (int i = 0; i < amount;i++) {
    //     LOG_PRINTK("%d ",temp_ptr[i]);
    // }
    // LOG_PRINTK("\n");
    fs_close(&read_file);
    k_mutex_unlock(&append_mutex);

    return rc;
}

int write_to_file(uint8_t *data, uint32_t length)
{
    k_mutex_lock(&append_mutex, K_FOREVER);
    if (length == 0U || length > sizeof(append_cache) - append_cache_length) {
        k_mutex_unlock(&append_mutex);
        return -EINVAL;
    }

    memcpy(append_cache + append_cache_length, data, length);
    append_cache_length += length;

    if (append_cache_length < sizeof(append_cache)) {
        k_mutex_unlock(&append_mutex);
        return (int) length;
    }

    int rc = flush_audio_file_unlocked(false);
    k_mutex_unlock(&append_mutex);
    return rc < 0 ? rc : (int) length;
}

int flush_audio_file(bool close_file)
{
    k_mutex_lock(&append_mutex, K_FOREVER);
    int rc = flush_audio_file_unlocked(close_file);
    k_mutex_unlock(&append_mutex);
    return rc;
}

static int flush_audio_file_unlocked(bool close_file)
{
    int rc;

    if (append_cache_length > 0U) {
        if (!append_file_initialized) {
            fs_file_t_init(&append_file);
            append_file_initialized = true;
        }
        if (!append_file_open) {
            rc = fs_open(&append_file, write_buffer, FS_O_WRITE | FS_O_APPEND);
            if (rc < 0) {
                return rc;
            }
            append_file_open = true;
        }

        rc = fs_write(&append_file, append_cache, append_cache_length);
        if (rc < 0) {
            return rc;
        }
        if ((size_t) rc != append_cache_length) {
            return -EIO;
        }
        append_cache_length = 0U;
    }

    if (append_file_open) {
        rc = fs_sync(&append_file);
        if (rc < 0) {
            return rc;
        }
        if (close_file) {
            rc = fs_close(&append_file);
            if (rc < 0) {
                return rc;
            }
            append_file_open = false;
        }
    }

    return 0;
}

int initialize_audio_file(uint8_t num)
{
    char *header = generate_new_audio_header(num);
    if (header == NULL) {
        return -1;
    }
    int rc = create_file(header);
    k_free(header);
    return rc;
}

char *generate_new_audio_header(uint8_t num)
{
    if (num > 99)
        return NULL;
    char *ptr_ = k_malloc(14);
    ptr_[0] = 'a';
    ptr_[1] = 'u';
    ptr_[2] = 'd';
    ptr_[3] = 'i';
    ptr_[4] = 'o';
    ptr_[5] = '/';
    ptr_[6] = 'a';
    ptr_[7] = 48 + (num / 10);
    ptr_[8] = 48 + (num % 10);
    ptr_[9] = '.';
    ptr_[10] = 't';
    ptr_[11] = 'x';
    ptr_[12] = 't';
    ptr_[13] = '\0';

    return ptr_;
}

int get_file_contents(struct fs_dir_t *zdp, struct fs_dirent *entry)
{
    if (zdp->mp->fs->readdir(zdp, entry)) {
        return -1;
    }
    if (entry->name[0] == 0) {
        return 0;
    }
    int count = 0;
    file_num_array[count] = entry->size;
    LOG_INF("file numarray %d %d ", count, file_num_array[count]);
    LOG_INF("file name is %s ", entry->name);
    count++;
    while (zdp->mp->fs->readdir(zdp, entry) == 0) {
        if (entry->name[0] == 0) {
            break;
        }
        file_num_array[count] = entry->size;
        LOG_INF("file numarray %d %d ", count, file_num_array[count]);
        LOG_INF("file name is %s ", entry->name);
        count++;
    }
    return count;
}
// we should clear instead of delete since we lose fifo structure
int clear_audio_file(uint8_t num)
{
    int flush_rc = flush_audio_file(true);
    if (flush_rc < 0) {
        return flush_rc;
    }

    char *clear_header = generate_new_audio_header(num);
    snprintf(current_full_path, sizeof(current_full_path), "%s%s", disk_mount_pt, clear_header);
    k_free(clear_header);
    int res = fs_unlink(current_full_path);
    if (res) {
        LOG_ERR("error deleting file");
        return -1;
    }

    char *create_file_header = generate_new_audio_header(num);
    k_msleep(10);
    res = create_file(create_file_header);
    k_free(create_file_header);
    if (res) {
        LOG_ERR("error creating file");
        return -1;
    }

    return 0;
}

int delete_audio_file(uint8_t num)
{
    int flush_rc = flush_audio_file(true);
    if (flush_rc < 0) {
        return flush_rc;
    }

    char *ptr = generate_new_audio_header(num);
    snprintf(current_full_path, sizeof(current_full_path), "%s%s", disk_mount_pt, ptr);
    k_free(ptr);
    int res = fs_unlink(current_full_path);
    if (res) {
        LOG_PRINTK("error deleting file in delete\n");
        return -1;
    }

    return 0;
}
// the nuclear option.
int clear_audio_directory()
{
    if (file_count == 1) {
        int res = clear_audio_file(1);
        if (res) {
            return res;
        }
        file_num_array[0] = 0;
        file_num_array[1] = 0;
        if (save_offset(0)) {
            return -1;
        }
        if (move_read_pointer(1) || move_write_pointer(1)) {
            return -1;
        }
        return 0;
    }
    // check if all files are zero
    //  char* path_ = "/SD:/audio";
    //  clear_audio_file(file_count);
    int res = 0;
    for (uint8_t i = file_count; i > 0; i--) {
        res = delete_audio_file(i);
        k_msleep(10);
        if (res) {
            LOG_PRINTK("error on %d\n", i);
            return -1;
        }
    }
    res = fs_unlink("/SD:/audio");
    if (res) {
        LOG_ERR("error deleting file");
        return -1;
    }
    res = fs_mkdir("/SD:/audio");
    if (res) {
        LOG_ERR("failed to make directory");
        return -1;
    }
    res = create_file("audio/a01.txt");
    if (res) {
        LOG_ERR("failed to make new file in directory files");
        return -1;
    }
    LOG_ERR("done with clearing");

    file_count = 1;
    file_num_array[0] = 0;
    file_num_array[1] = 0;
    if (save_offset(0) || move_read_pointer(1) || move_write_pointer(1)) {
        return -1;
    }
    return 0;
    // if files are cleared, then directory is oked for destrcution.
}

int save_offset(uint32_t offset)
{
    uint8_t buf[4] = {offset & 0xFF, (offset >> 8) & 0xFF, (offset >> 16) & 0xFF, (offset >> 24) & 0xFF};

    struct fs_file_t write_file;
    fs_file_t_init(&write_file);
    int res = fs_open(&write_file, "/SD:/info.txt", FS_O_WRITE | FS_O_CREATE);
    if (res) {
        LOG_ERR("error opening file %d", res);
        return -1;
    }
    res = fs_write(&write_file, &buf, 4);
    if (res < 0) {
        LOG_ERR("error writing file %d", res);
        fs_close(&write_file);
        return -1;
    }
    if (res != sizeof(buf)) {
        fs_close(&write_file);
        return -EIO;
    }
    fs_close(&write_file);
    return 0;
}

int get_offset()
{
    uint8_t buf[4];
    struct fs_file_t read_file;
    fs_file_t_init(&read_file);
    int rc = fs_open(&read_file, "/SD:/info.txt", FS_O_READ);
    if (rc < 0) {
        LOG_ERR("error opening file %d", rc);
        return -1;
    }
    rc = fs_seek(&read_file, 0, FS_SEEK_SET);
    if (rc < 0) {
        LOG_ERR("error seeking file %d", rc);
        return -1;
    }
    rc = fs_read(&read_file, &buf, 4);
    if (rc < 0) {
        LOG_ERR("error reading file %d", rc);
        return -1;
    }
    fs_close(&read_file);
    if (rc != sizeof(buf)) {
        return -EIO;
    }
    uint32_t stored_offset = (uint32_t) buf[0] | ((uint32_t) buf[1] << 8) | ((uint32_t) buf[2] << 16) |
                             ((uint32_t) buf[3] << 24);
    LOG_INF("get offset is %u", stored_offset);

    return (int) stored_offset;
}

void sd_off()
{
    /* The BFF stays powered; suspend only the SPI controller. */
    int flush_rc = flush_audio_file(true);
    if (flush_rc < 0) {
        LOG_ERR("failed to flush audio before SD suspend: %d", flush_rc);
    }
    const struct device *spi_dev = DEVICE_DT_GET(DT_NODELABEL(spi2));
    if (device_is_ready(spi_dev)) {
        pm_device_action_run(spi_dev, PM_DEVICE_ACTION_SUSPEND);
    }
    sd_enabled = false;
}

void sd_on()
{
    const struct device *spi_dev = DEVICE_DT_GET(DT_NODELABEL(spi2));
    if (device_is_ready(spi_dev)) {
        pm_device_action_run(spi_dev, PM_DEVICE_ACTION_RESUME);
    }
    sd_enabled = true;
}

bool is_sd_on()
{
    return sd_enabled && sd_mounted;
}
