#!/usr/bin/env bash
set -euo pipefail

theme_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
destination="${XDG_DATA_HOME:-$HOME/.local/share}/icons/Marvin-Red-Circles"

if [[ "${1:-}" == "--rebuild" ]]; then
    "$theme_root/tools/build-theme.py"
fi
mkdir -p "$(dirname "$destination")"
rsync -a --delete --exclude '.git/' "$theme_root/" "$destination/"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f "$destination" >/dev/null 2>&1 || true
fi

printf 'Installed Marvin Red Circles in %s\n' "$destination"
printf 'Select it in System Settings > Appearance > Icons.\n'
