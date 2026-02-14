#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${NADES_DATA_DIR:-$SCRIPT_DIR/data}"

cd "$SCRIPT_DIR"
python3 scrape_nades.py --outdir "$DATA_DIR" 2>&1

# Invalidate nade cache by restarting the service
if command -v systemctl &>/dev/null; then
  sudo systemctl restart cs-nades
fi

echo "Update complete: $(date)"
