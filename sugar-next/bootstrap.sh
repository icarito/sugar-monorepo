#!/bin/sh
# Bootstrap Sugar Next on any Linux distro: pip install + desktop entry.
#
# Requires GTK4 and PyGObject from your distro (pip cannot build PyGObject
# without GObject headers):
#   Fedora:      sudo dnf install python3-gobject gtk4
#   Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0
#   Arch:        sudo pacman -S python-gobject gtk4

set -eu

here="$(cd "$(dirname "$0")" && pwd)"

echo "Installing sugar-next from $here ..."
pip install --user "$here"

apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$apps_dir"
cat > "$apps_dir/org.sugarlabs.SugarNext.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Sugar Next
Comment=Modern shell for Sugar Labs
Exec=sugar-next
Icon=org.sugarlabs.SugarNext
Categories=System;Education;
EOF

echo "Done. Launch with 'sugar-next' or from your app menu."
echo "Extensions go in \${XDG_DATA_HOME:-~/.local/share}/sugar-next/extensions/"
