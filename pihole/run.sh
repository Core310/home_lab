#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v ansible-playbook &> /dev/null; then
    echo "Error: ansible-playbook could not be found."
    echo "Please install Ansible by running: sudo apt update && sudo apt install -y ansible"
    exit 1
fi

if [ "$EUID" -ne 0 ] && [[ "$*" != *"-K"* ]] && [[ "$*" != *"--ask-become-pass"* ]]; then
    exec sudo -E ansible-playbook -i localhost, -c local site.yml "$@"
else
    ansible-playbook -i localhost, -c local site.yml "$@"
fi
