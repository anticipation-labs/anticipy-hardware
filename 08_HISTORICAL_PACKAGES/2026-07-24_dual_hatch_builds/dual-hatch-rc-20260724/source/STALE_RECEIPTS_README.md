# Two receipt files in this directory are STALE

`ANTICIPY_SOURCE_RECEIPT.json` and `DUAL_HATCH_RECEIPT.json` were copied
verbatim from `/Users/omarebrahim/anticipation-builds/dual-hatch-20260724/source/`
when this tree was created. They describe **that** tree.

They are still accurate about everything except the low-frequency clock,
because the only delta between the two source trees is six Kconfig lines in
`prj_xiao_ble_sense_devkitv2-adafruit.conf`:

```
CONFIG_CLOCK_CONTROL_NRF_K32SRC_RC=y
CONFIG_CLOCK_CONTROL_NRF_K32SRC_RC_CALIBRATION=y
CONFIG_CLOCK_CONTROL_NRF_CALIBRATION_PERIOD=4000
CONFIG_CLOCK_CONTROL_NRF_CALIBRATION_MAX_SKIP=1
CONFIG_CLOCK_CONTROL_NRF_CALIBRATION_TEMP_DIFF=2
CONFIG_CLOCK_CONTROL_NRF_K32SRC_500PPM=y
```

`diff -rq` over the two source trees reports exactly one differing file.

Their `critical_file_sha256` / `changed_files_sha256` maps therefore still
match for every file **except** the prj.conf.

The authoritative receipt for this tree and its build is:

    ../RC_BUILD_RECEIPT.json
