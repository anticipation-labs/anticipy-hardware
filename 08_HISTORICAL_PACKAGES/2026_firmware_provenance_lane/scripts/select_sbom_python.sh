#!/usr/bin/env bash
# Print the one Python executable that satisfies the firmware SPDX runtime lock.
set -euo pipefail

script_dir="${BASH_SOURCE[0]%/*}"
repo_root="$(cd "$script_dir/../.." && pwd)"
cd "$repo_root"

runtime_marker="ANTICIPY_FIRMWARE_SPDX_RUNTIME_OK"
runtime_probe='import sys; sys.path.insert(0, "firmware/scripts"); from spdx_sbom import sbom_readiness; ready, _ = sbom_readiness(); print("ANTICIPY_FIRMWARE_SPDX_RUNTIME_OK") if ready else None; raise SystemExit(0 if ready else 1)'

matches_runtime_lock() {
  local candidate="$1"
  local observed
  [[ -n "$candidate" && -x "$candidate" ]] || return 1
  observed="$(
    PYTHONPATH= PYTHONNOUSERSITE=1 \
      "$candidate" -E -s -c "$runtime_probe" 2>/dev/null
  )" || return 1
  [[ "$observed" == "$runtime_marker" ]]
}

requested="${ANTICIPY_FIRMWARE_PYTHON:-}"
if [[ -n "$requested" ]]; then
  if matches_runtime_lock "$requested"; then
    printf '%s\n' "$requested"
    exit 0
  fi
  echo "ANTICIPY_FIRMWARE_PYTHON does not satisfy the pinned firmware SPDX validator runtime." >&2
  exit 2
fi

for candidate in \
  "$(command -v python3.10 2>/dev/null || true)" \
  "$(command -v python3 2>/dev/null || true)"
do
  if matches_runtime_lock "$candidate"; then
    printf '%s\n' "$candidate"
    exit 0
  fi
done

echo "No Python satisfies the pinned firmware SPDX validator runtime; set ANTICIPY_FIRMWARE_PYTHON to an exact match." >&2
exit 2
