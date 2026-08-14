#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure script is run with sudo if not already root
if [ "$EUID" -ne 0 ]; then
  exec sudo -E bash "$0" "$@"
fi

# Run the Ansible playbook locally against localhost
ansible-playbook -i localhost, -c local "${SCRIPT_DIR}/site.yml" "$@"
