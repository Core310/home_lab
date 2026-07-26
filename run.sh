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
echo "You can now run the Ansible playbook to deploy the FOSS stack:"
echo "ansible-playbook -i localhost, -c local anime_torrent_streamer/site.yml --ask-become-pass"
