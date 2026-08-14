#!/bin/bash
set -euo pipefail

# Unified Homelab Database & Critical Config Backup Script
MIRROR_BASE="/home/arika/mirrors/databases"
MIRROR_LATEST="$MIRROR_BASE/latest"
MIRROR_ARCHIVE="$MIRROR_BASE/archive"
TARGET_USER="arika"
TARGET_GROUP="arika"
RETENTION_DAYS=14
DATE_TAG=$(date +"%Y-%m-%d")
TEMP_DIR=$(mktemp -d)

trap 'rm -rf "$TEMP_DIR"' EXIT

mkdir -p "$MIRROR_LATEST" "$MIRROR_ARCHIVE" "$TEMP_DIR"

backup_file() {
    local src="$1"
    local rel_dest="$2"
    local dest_dir
    dest_dir="$TEMP_DIR/$(dirname "$rel_dest")"
    mkdir -p "$dest_dir"

    if [ ! -f "$src" ]; then
        return 0
    fi

    # Try SQLite atomic backup first
    if sqlite3 "$src" ".backup '$TEMP_DIR/$rel_dest'" 2>/dev/null; then
        return 0
    else
        # For non-SQLite binary databases (LiteDB, BoltDB) or key files, copy directly
        cp -f "$src" "$TEMP_DIR/$rel_dest"
    fi
}

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Homelab Database Backup..."

# 1. Vaultwarden (Passwords & Keys)
backup_file "/home/arika/D/docs/home_lab/personal_cloud/data/vaultwarden/db.sqlite3" "vaultwarden/db.sqlite3"
backup_file "/home/arika/D/docs/home_lab/personal_cloud/data/vaultwarden/rsa_key.pem" "vaultwarden/rsa_key.pem"

# 2. Life Management (Mealie, LubeLogger, Speedtest)
backup_file "/home/arika/D/docs/home_lab/life_management/data/mealie/mealie.db" "mealie/mealie.db"
backup_file "/home/arika/D/docs/home_lab/life_management/data/lubelogger/data/cartracker.db" "lubelogger/cartracker.db"
backup_file "/home/arika/D/docs/home_lab/life_management/data/speedtest_tracker/database/database.sqlite" "speedtest/database.sqlite"

# 3. Media & Indexers (Sonarr, Prowlarr, Lidarr, Jellyfin)
backup_file "/home/arika/D/docs/home_lab/anime_torrent_streamer/config/sonarr/sonarr.db" "sonarr/sonarr.db"
backup_file "/home/arika/D/docs/home_lab/anime_torrent_streamer/config/prowlarr/prowlarr.db" "prowlarr/prowlarr.db"
backup_file "/home/arika/D/docs/home_lab/anime_torrent_streamer/config/jellyfin/data/data/jellyfin.db" "jellyfin/jellyfin.db"
backup_file "/home/arika/D/docs/home_lab/music_stack/config/lidarr/lidarr.db" "lidarr/lidarr.db"
backup_file "/home/arika/D/docs/home_lab/music_stack/config/filebrowser/filebrowser.db" "filebrowser/filebrowser.db"

# 4. DNS & Adblocking (Pi-hole)
backup_file "/home/arika/D/docs/home_lab/pihole/etc-pihole/pihole-FTL.db" "pihole/pihole-FTL.db"
backup_file "/home/arika/D/docs/home_lab/pihole/etc-pihole/gravity.db" "pihole/gravity.db"

# Sync latest staging to mirror latest
rsync -a --delete "$TEMP_DIR/" "$MIRROR_LATEST/"

# Create daily compressed archive
ARCHIVE_FILE="$MIRROR_ARCHIVE/homelab_databases_${DATE_TAG}.tar.gz"
tar -czf "$ARCHIVE_FILE" -C "$MIRROR_LATEST" .
cp -f "$ARCHIVE_FILE" "$MIRROR_ARCHIVE/homelab_databases_latest.tar.gz"

# Also maintain vaultwarden-specific mirror for convenience
mkdir -p /home/arika/mirrors/vaultwarden/latest /home/arika/mirrors/vaultwarden/archive
if [ -d "$MIRROR_LATEST/vaultwarden" ]; then
    rsync -a "$MIRROR_LATEST/vaultwarden/" /home/arika/mirrors/vaultwarden/latest/
    cp -f "$ARCHIVE_FILE" "/home/arika/mirrors/vaultwarden/archive/vaultwarden_${DATE_TAG}.tar.gz"
    cp -f "$ARCHIVE_FILE" "/home/arika/mirrors/vaultwarden/archive/vaultwarden_latest.tar.gz"
fi

# Rotate archives older than retention days (14 days)
find "$MIRROR_ARCHIVE" -name "homelab_databases_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
find "/home/arika/mirrors/vaultwarden/archive" -name "vaultwarden_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

# Fix permissions
chown -R "$TARGET_USER:$TARGET_GROUP" "/home/arika/mirrors"
chmod -R 750 "/home/arika/mirrors"

ARCHIVE_SIZE=$(du -h "$ARCHIVE_FILE" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Homelab Database Backup completed successfully. (Size: $ARCHIVE_SIZE)"
