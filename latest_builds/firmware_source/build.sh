#!/usr/bin/env bash
set -euo pipefail
bench_root=$(cd "$(dirname "$0")" && pwd)
bench_sdk=${ANTICIPY_NCS_ROOT:-/opt/nordic/ncs/v2.7.0}
bench_tc=${ANTICIPY_TOOLCHAIN_ROOT:-/opt/nordic/ncs/toolchains/f8037e9b83}
bench_build=${ANTICIPY_E1P1_BUILD_ROOT:-"$bench_root/build"}
export PATH="$bench_tc/bin:$bench_tc/usr/bin:$bench_tc/usr/local/bin:$bench_tc/opt/bin:$bench_tc/opt/zephyr-sdk/arm-zephyr-eabi/bin:$PATH"
export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR="$bench_tc/opt/zephyr-sdk"
export ZEPHYR_BASE="$bench_sdk/zephyr"
export PYTHONPYCACHEPREFIX="$bench_build/python-cache"
export XDG_CACHE_HOME="$bench_build/cache"
mkdir -p "$bench_build" "$bench_root/receipts"
cd "$bench_sdk"
west build --pristine always -b anticipy_e1/nrf52840 -d "$bench_build/target" "$bench_root/app" -- \
 "-DUSER_CACHE_DIR=$bench_build/cache" 2>&1 | tee "$bench_root/receipts/target_build.log"
