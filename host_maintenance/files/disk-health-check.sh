#!/bin/bash
set -euo pipefail

LOG_FILE="/var/log/disk-health.log"
ALERT_FILE="/var/log/disk-health-alerts.log"
HAS_ERROR=0

# Dynamically discover all connected SMART-capable physical drives
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

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running SMART disk health check across all drives (${DRIVES[*]})..." >> "$LOG_FILE"

for drive in "${DRIVES[@]}"; do
    if [ -z "$drive" ] || [ ! -b "$drive" ]; then
        continue
    fi

    MODEL=$(smartctl -i "$drive" 2>&1 | grep -i "Device Model\|Model Number" | awk -F: '{print $2}' | xargs || echo "Unknown Model")

    # 1. Check overall health status
    HEALTH_OUTPUT=$(smartctl -H "$drive" 2>&1 || true)
    if echo "$HEALTH_OUTPUT" | grep -q "PASSED"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Drive $drive ($MODEL): Overall Health PASSED" >> "$LOG_FILE"
    else
        MSG="CRITICAL: Drive $drive ($MODEL) SMART Health Status FAILED!"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $MSG" | tee -a "$LOG_FILE" "$ALERT_FILE"
        logger -p daemon.crit "$MSG"
        HAS_ERROR=1
    fi

    # 2. Check for bad / pending / reallocated sectors
    ATTR_OUTPUT=$(smartctl -A "$drive" 2>&1 || true)
    
    # Reallocated Sector Count (Attribute 5)
    REALLOCATED=$(echo "$ATTR_OUTPUT" | awk '$1 == "5" {print $10}' || true)
    if [ -n "$REALLOCATED" ] && [ "$REALLOCATED" -gt 0 ] 2>/dev/null; then
        MSG="WARNING: Drive $drive ($MODEL) has $REALLOCATED reallocated sectors!"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $MSG" | tee -a "$LOG_FILE" "$ALERT_FILE"
        logger -p daemon.warning "$MSG"
        HAS_ERROR=1
    fi

    # Current Pending Sector Count (Attribute 197)
    PENDING=$(echo "$ATTR_OUTPUT" | awk '$1 == "197" {print $10}' || true)
    if [ -n "$PENDING" ] && [ "$PENDING" -gt 0 ] 2>/dev/null; then
        MSG="CRITICAL: Drive $drive ($MODEL) has $PENDING unreadable/pending sectors!"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $MSG" | tee -a "$LOG_FILE" "$ALERT_FILE"
        logger -p daemon.crit "$MSG"
        HAS_ERROR=1
    fi

    # Offline Uncorrectable (Attribute 198)
    OFFLINE_UNC=$(echo "$ATTR_OUTPUT" | awk '$1 == "198" {print $10}' || true)
    if [ -n "$OFFLINE_UNC" ] && [ "$OFFLINE_UNC" -gt 0 ] 2>/dev/null; then
        MSG="CRITICAL: Drive $drive ($MODEL) has $OFFLINE_UNC offline uncorrectable sectors!"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $MSG" | tee -a "$LOG_FILE" "$ALERT_FILE"
        logger -p daemon.crit "$MSG"
        HAS_ERROR=1
    fi
done

if [ "$HAS_ERROR" -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] All connected drives healthy. No bad sectors found." >> "$LOG_FILE"
fi
