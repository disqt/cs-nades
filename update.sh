#!/bin/bash
set -e
cd $APP_DIR
python3 scrape_nades.py --outdir $DATA_DIR 2>&1
# Invalidate nade cache by restarting the service
sudo systemctl restart cs-nades
echo "Update complete: $(date)"
