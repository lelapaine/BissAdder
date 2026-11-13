#!/bin/sh
# Builds enigma2-plugin-extensions-bissadder_<version>_all.ipk  (needs: tar, ar)
# Run from the repo root:  sh build_ipk.sh
VER="1.0"
PKG="enigma2-plugin-extensions-bissadder"
W="$(mktemp -d)"
D="$W/data"; C="$W/control"
mkdir -p "$D/usr/lib/enigma2/python/Plugins/Extensions" "$C"
cp -r BissAdder "$D/usr/lib/enigma2/python/Plugins/Extensions/BissAdder"
find "$D" -name '__pycache__' -prune -exec rm -rf {} \; 2>/dev/null
cat > "$C/control" <<EOT
Package: $PKG
Version: $VER
Architecture: all
Section: extra
Priority: optional
Maintainer: BissAdder
Description: BISS Adder - add BISS keys (F hash 00/01) for the current channel to SoftCam.Key
EOT
cat > "$C/postinst" <<'EOT'
#!/bin/sh
CONF=/etc/tuxbox/config/BissAdder.conf
EX=/usr/lib/enigma2/python/Plugins/Extensions/BissAdder/BissAdder.conf.example
mkdir -p /etc/tuxbox/config
[ -f "$CONF" ] || cp "$EX" "$CONF"
echo "BissAdder installed. Restart the GUI."
exit 0
EOT
chmod 755 "$C/postinst"
echo 2.0 > "$W/debian-binary"
( cd "$D" && tar --owner=0 --group=0 -czf "$W/data.tar.gz" . )
( cd "$C" && tar --owner=0 --group=0 -czf "$W/control.tar.gz" . )
( cd "$W" && ar r "${PKG}_${VER}_all.ipk" debian-binary control.tar.gz data.tar.gz )
cp "$W/${PKG}_${VER}_all.ipk" .
rm -rf "$W"
echo "Built ${PKG}_${VER}_all.ipk"
