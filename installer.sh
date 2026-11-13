#!/bin/sh
# BissAdder one-line installer for Enigma2 receivers.
# Usage (one line, in telnet/SSH):
#   wget -q --no-check-certificate -O - https://raw.githubusercontent.com/YOUR_USER/BissAdder/main/installer.sh | sh
REPO="lelapaine/BissAdder"
BRANCH="main"

PLUGIN_DIR="${PLUGIN_DIR:-/usr/lib/enigma2/python/Plugins/Extensions}"
CONF_DIR="${CONF_DIR:-/etc/tuxbox/config}"
TMP="/tmp/bissadder_install"

fail() { echo "ERROR: $1"; rm -rf "$TMP"; exit 1; }

rm -rf "$TMP"; mkdir -p "$TMP" || fail "cannot create $TMP"

if [ -n "$LOCAL_SRC" ]; then
    SRC="$LOCAL_SRC"
else
    echo "Downloading BissAdder..."
    wget -q --no-check-certificate -O "$TMP/src.tar.gz" "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" \
        || fail "download failed (check internet / repo name)"
    tar -xzf "$TMP/src.tar.gz" -C "$TMP" || fail "cannot unpack the download"
    SRC=$(ls -d "$TMP"/*/ 2>/dev/null | head -n 1)
fi

[ -f "$SRC/BissAdder/plugin.py" ] || fail "plugin files not found in the download"

echo "Installing plugin..."
mkdir -p "$PLUGIN_DIR" "$CONF_DIR"
rm -rf "$PLUGIN_DIR/BissAdder"
cp -r "$SRC/BissAdder" "$PLUGIN_DIR/BissAdder" || fail "copy failed"
find "$PLUGIN_DIR/BissAdder" -name '*.pyc' -delete 2>/dev/null

if [ ! -f "$CONF_DIR/BissAdder.conf" ]; then
    cp "$PLUGIN_DIR/BissAdder/BissAdder.conf.example" "$CONF_DIR/BissAdder.conf"
    echo "Config created: $CONF_DIR/BissAdder.conf"
else
    echo "Config kept: $CONF_DIR/BissAdder.conf"
fi

rm -rf "$TMP"
echo "BissAdder installed."
if [ -z "$NO_RESTART" ]; then
    echo "Restarting the GUI..."
    sleep 2
    killall -9 enigma2
fi
exit 0
