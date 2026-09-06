#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FILE="$SCRIPT_DIR/../Anticipy_Founder_EVT_v0.9.0.uf2"
DEST="${1:-/Volumes/XIAO-SENSE}"

if [ ! -f "$FILE" ]; then
echo "Firmware file not found: $FILE"
  exit 1
fi

if [ ! -d "$DEST" ]; then
  echo "XIAO boot drive not mounted at $DEST"
  echo "Double-tap reset, then try again. You may pass a different mount path as argument 1."
  exit 1
fi

cp "$FILE" "$DEST"
echo "Copied $(basename "$FILE") to $DEST"
