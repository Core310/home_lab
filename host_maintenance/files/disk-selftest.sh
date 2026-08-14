#!/bin/bash
set -euo pipefail

TEST_TYPE="${1:-short}" # "short" or "long"
LOG_FILE="/var/log/disk-health.log"

get_drives() {
    local drives=()
    if command -v smartctl &>/dev/null; then
        while IFS= read -r line; do
            [ -n "$line" ] && drives+=("$line")
        done < <(smartctl --scan 2>/dev/null | awk '{print $1}')
    fi
    if [ ${#drives[@]} -eq 0 ]; then
        while IFS= read -r line; do
            [ -n "$line" ] && drives+=("/dev/$line")
        done < <(lsblk -d -n -o NAME,TYPE 2>/dev/null | awk '$2=="disk"{print $1}')
    fi
    echo "${drives[@]}"
}

mapfile -t DRIVES < <(get_drives | tr ' ' '\n')

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initiating SMART $TEST_TYPE self-test across all drives (${DRIVES[*]})..." >> "$LOG_FILE"

for drive in "${DRIVES[@]}"; do
    if [ -n "$drive" ] && [ -b "$drive" ]; then
        smartctl -t "$TEST_TYPE" "$drive" >> "$LOG_FILE" 2>&1 || true
    fi
done
