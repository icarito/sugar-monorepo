#!/bin/sh
# Bootstrap Sugar Next on any Linux distro: venv install + desktop entry.
#
# Requires GTK4 and PyGObject from your distro (pip cannot build PyGObject
# without GObject headers):
#   Fedora:      sudo dnf install python3-gobject gtk4
#   Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0
#   Arch:        sudo pacman -S python-gobject gtk4
#
# Installs into a dedicated venv (--system-site-packages, so PyGObject
# resolves against the distro's compiled GI bindings) rather than
# `pip install --user`, which fails outright on PEP 668
# externally-managed distros such as Arch.

set -eu

here="$(cd "$(dirname "$0")" && pwd)"
venv_dir="${XDG_DATA_HOME:-$HOME/.local/share}/sugar-next/venv"

echo "Installing sugar-next from $here into $venv_dir ..."
python3 -m venv --system-site-packages "$venv_dir"
"$venv_dir/bin/pip" install --upgrade pip
"$venv_dir/bin/pip" install "$here"

exec_path="$venv_dir/bin/sugar-next"

bin_dir="${XDG_BIN_HOME:-$HOME/.local/bin}"
mkdir -p "$bin_dir"
ln -sf "$exec_path" "$bin_dir/sugar-next"
case ":$PATH:" in
	*":$bin_dir:"*) ;;
	*) echo "Note: $bin_dir is not on your PATH. Add it, or run sugar-next via $exec_path" >&2 ;;
esac

apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$apps_dir"
cat > "$apps_dir/org.sugarlabs.SugarNext.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Sugar Next
Comment=A Learning Shell for Everyday Computing
Exec=$exec_path
Icon=org.sugarlabs.SugarNext
Categories=System;Education;
EOF

echo "Done. Launch with 'sugar-next' or from your app menu."
echo "Extensions go in \${XDG_DATA_HOME:-~/.local/share}/sugar-next/extensions/"
