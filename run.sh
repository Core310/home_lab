#!/bin/bash
set -e

echo "========================================"
echo " Starting GSD FOSS Stack Bootstrap... "
echo "========================================"

echo "Updating system packages..."
sudo apt-get update

echo "Installing prerequisites (Ansible, Git, Python)..."
sudo apt-get install -y software-properties-common git ansible python3-pip

echo "========================================"
echo " Prerequisites Installed! "
echo "========================================"
echo "You can now run any stack using its run.sh wrapper script:"
echo "  ./gateway/run.sh           # Caddy, Authentik, Homepage"
echo "  ./personal_cloud/run.sh    # Vaultwarden, Immich, Gitea"
echo "  ./life_management/run.sh   # Mealie, LubeLogger, Christmas Community, Speedtest"
echo "  ./utility_stack/run.sh     # Portainer, Beszel, BentoPDF, VERT"
echo "  ./anime_torrent_streamer/run.sh # qBittorrent, Sonarr, Prowlarr, Jellyfin"
echo "  ./music_stack/run.sh       # Lidarr, Filebrowser, Dufs"
echo "  ./pihole/run.sh            # Pi-hole & DNSCrypt"
