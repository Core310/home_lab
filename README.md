# FOSS Anime Homelab Stack

Welcome to the ultimate Infrastructure-as-Code (IaC) media server deployment! This repository contains the automation required to spin up a fully isolated, robust, and automated media pipeline on your homelab. 

## What This Does

This setup transforms a bare linux machine into a fully functional media server, complete with network-wide ad-blocking and an automated acquisition pipeline. It utilizes **Ansible** as the provisioner and **Docker** (with Docker Compose) as the container engine.

The stack deploys the following isolated services:
- **Pi-hole**: Network-wide ad blocking and local DNS resolution (crucial for Tailscale MagicDNS routing).
- **qBittorrent**: The torrent downloader, strictly isolated to drop raw files in a designated download folder.
- **Prowlarr**: The indexer manager that searches the web for media and automatically syncs indexers to Sonarr.
- **Sonarr**: The TV show manager. It acts as the brain—searching for shows, grabbing torrents, sending them to qBittorrent, and ultimately organizing the finished files.
- **Jellyfin**: The FOSS media streaming server. It acts as your personal Netflix, scanning the final organized media folder to serve directly to your devices.

### Music & Management Stack (`music_stack/`)
- **Lidarr**: The high-res audio (FLAC) equivalent to Sonarr. Automates finding and organizing music.
- **Filebrowser**: A lightweight, modern web-based file manager for visually clicking and dragging files around your server via a web browser.
- **Dufs**: A blazing-fast Rust WebDAV server running silently so mobile apps (like Poweramp via a WebDAV client) can natively stream your server's audio library.

## How It Works: Ansible + Docker

**You only need to run the Ansible playbook.**

Here is what the Ansible playbook (`site.yml`) automates for you:
1. **Installs Prerequisites:** It automatically ensures `docker.io` and `docker-compose-v2` are installed on the host.
2. **Scaffolds the File System:** It creates the exact directory structures required on the host (`/opt/media`, `/opt/media/downloads`, `/opt/media/jellyfin`) with the correct user permissions (`1000:1000`) so the containers can read and write without access denied errors.
3. **Deploys the Code:** It creates the deployment folder (`/opt/foss_stack`) and copies your `docker-compose.yml` into it.
4. **Spins Up the Stack:** Finally, Ansible executes the `docker compose up -d` command for you. 

When the playbook finishes running, your entire infrastructure is online and humming.

## Deployment Instructions

### 1. Bare Metal Bootstrap (Optional)
If you are deploying this to a completely fresh Ubuntu server, simply execute the included bootstrap script. It will automatically update your packages and install the prerequisites (Ansible, Git, Python):

```bash
chmod +x run.sh
./run.sh
```

### 2. Stack Deployment
Deploy any stack simply by running its respective `run.sh` script:

```bash
# 1. Gateway & Identity (Caddy, Authentik, Homepage)
./gateway/run.sh

# 2. Personal Cloud (Vaultwarden, Immich, Gitea)
./personal_cloud/run.sh

# 3. Life Management (Mealie, LubeLogger, Christmas Community, Speedtest)
./life_management/run.sh

# 4. Utility Stack (Portainer, Beszel, BentoPDF, VERT)
./utility_stack/run.sh

# 5. Anime & Torrent Stack (qBittorrent, Sonarr, Prowlarr, Jellyfin)
./anime_torrent_streamer/run.sh

# 6. Music & WebDAV Stack (Lidarr, Filebrowser, Dufs)
./music_stack/run.sh

# 7. DNS & Network Security Stack (Pi-hole, DNSCrypt-Proxy)
./pihole/run.sh

# 8. Automated Job Application Pipeline (ApplyPilot)
./job_applier/run.sh
```

---

## Port & Subdomain Reference (`*.somethingsomething.fyi`)

| Port | Service | Subdomain | Description |
| :--- | :--- | :--- | :--- |
| **80 / 443** | **Caddy** | `*.somethingsomething.fyi` | Reverse Proxy with Auto-TLS / Tailscale |
| **9302** | **Homepage** | `dash.somethingsomething.fyi` | Central Homelab Dashboard |
| **9300 / 9301** | **Authentik** | `auth.somethingsomething.fyi` | Single Sign-On (SSO) & 2FA Provider |
| **9400** | **Vaultwarden** | `vault.somethingsomething.fyi` | Bitwarden Password Manager |
| **9401** | **Immich** | `photos.somethingsomething.fyi` | High-Performance Photo/Video Cloud |
| **9402** (2222 ssh) | **Gitea** | `git.somethingsomething.fyi` | Self-Hosted Git & Code Hosting |
| **9500** | **Mealie** | `recipes.somethingsomething.fyi` | Recipe Manager & Meal Planner |
| **9501** | **LubeLogger** | `garage.somethingsomething.fyi` | Vehicle Maintenance & Fuel Tracker |
| **9502** | **Christmas Community**| `wishlist.somethingsomething.fyi` | Holiday Wishlists & Secret Santa |
| **9503** | **Speedtest Tracker** | `speedtest.somethingsomething.fyi` | Automated Bandwidth & Latency Grapher |
| **9003** | **Jellyfin** | `anime.somethingsomething.fyi` | Streaming Media Server |
| **9000** | **qBittorrent** | `torrents.somethingsomething.fyi` | BitTorrent Client |
| **9001** | **Sonarr** | `sonarr.somethingsomething.fyi` | TV & Anime Automation |
| **9002** | **Prowlarr** | `prowlarr.somethingsomething.fyi` | Torrent Indexer Aggregator |
| **9101** | **Lidarr** | `music.somethingsomething.fyi` | Music Automation |
| **9100** | **Filebrowser** | `files.somethingsomething.fyi` | Browser-based File Explorer |
| **9102** | **Dufs** | `webdav.somethingsomething.fyi` | Fast Rust WebDAV Server |
| **9200 / 9201** | **Portainer** | `portainer.somethingsomething.fyi` | Docker Container UI |
| **9202** | **Beszel Hub** | `status.somethingsomething.fyi` | Server Metrics & Hardware Monitor |
| **9203** | **BentoPDF** | `pdf.somethingsomething.fyi` | Privacy-focused PDF Tools |
| **9204** | **VERT** | `convert.somethingsomething.fyi` | Offline Universal File Converter |
| **53 / 80** | **Pi-hole** | `pihole.somethingsomething.fyi` | DNS Sinkhole & Adblocker |

