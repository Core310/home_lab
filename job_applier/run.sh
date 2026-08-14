#!/usr/bin/env bash
# ==============================================================================
# ApplyPilot Automated Job Pipeline Deployer & Runner
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\033[1;36m========================================================\033[0m"
echo -e "\033[1;36m       Deploying ApplyPilot Job Application Stack        \033[0m"
echo -e "\033[1;36m========================================================\033[0m"

# Elevate privileges if not already root
if [ "$EUID" -ne 0 ]; then
    echo -e "\033[1;33m[INFO]\033[0m Elevating permissions with sudo..."
    exec sudo bash "$0" "$@"
fi

# Ensure Ansible is installed
if ! command -v ansible-playbook &>/dev/null; then
    echo -e "\033[1;33m[INFO]\033[0m Ansible not found. Installing ansible..."
    apt-get update && apt-get install -y ansible
fi

echo -e "\033[1;32m[INFO]\033[0m Running Ansible Playbook: site.yml..."
ansible-playbook -i "localhost," -c local site.yml

echo -e "\n\033[1;32m========================================================\033[0m"
echo -e "\033[1;32m    ApplyPilot Job Application Pipeline Ready!          \033[0m"
echo -e "\033[1;32m========================================================\033[0m"
echo -e "Application directory: \033[1;34m$SCRIPT_DIR/app\033[0m"
echo -e "CSV Tracker:           \033[1;34m$SCRIPT_DIR/app/jobs.csv\033[0m"
echo -e "Resume File:           \033[1;34m$SCRIPT_DIR/app/plain_text_resume.yaml\033[0m"
echo -e "\nTo run the batch job applier, execute:"
echo -e "  \033[1;33mcd $SCRIPT_DIR/app && ./run_batch.sh\033[0m"
echo -e "To run in dry-run mode (simulation):"
echo -e "  \033[1;33mcd $SCRIPT_DIR/app && ./run_batch.sh --dry-run\033[0m\n"
