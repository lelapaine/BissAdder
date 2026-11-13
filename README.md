# BissAdder

Enigma2 plugin: open it on a BISS channel, type the key with the remote, and it writes the
`F <hash> 00 <key>` / `F <hash> 01 <key>` lines into `SoftCam.Key` for you (the hash is
calculated automatically from the channel). Light, no background process, Python 2 and 3.

## Install (one line, telnet/SSH)

```
wget -q --no-check-certificate -O - https://raw.githubusercontent.com/YOUR_USER/BissAdder/main/installer.sh | sh
```

The receiver GUI restarts at the end. The plugin appears in the Plugins menu and the
Extensions menu (blue button). To open it with a remote button: Hotkey setup -> pick a
button -> Extensions -> BISS Adder.

Backup: download the `.ipk` from the Releases page, copy it to `/tmp` and run
`opkg install /tmp/enigma2-plugin-extensions-bissadder_1.0_all.ipk`.

## Use

| Key | Action |
|---|---|
| 0-9 | type a digit, move on |
| UP / DOWN | cycle 0-9 and A-F |
| LEFT / RIGHT | move the cursor |
| YELLOW | switch between Key 00 and Key 01 |
| BLUE | copy Key 00 into Key 01 |
| RED | clear the field |
| GREEN / OK | save (then asks to restart the softcam) |

Key 01 can be left empty: only the `00` line is written.

## Settings

Edit `/etc/tuxbox/config/BissAdder.conf` (created by the installer):

```
key_file = /etc/tuxbox/config/SoftCam.Key
restart_cmd = /etc/init.d/softcam restart
```

- `key_file`: full path of your key file. Linux is case-sensitive, so `SoftCam.Key` and
  `softcam.key` are different files. If you leave it out, the plugin searches the usual
  folders (ignoring upper/lower case) and falls back to `/etc/tuxbox/config/SoftCam.Key`.
- `restart_cmd`: how to restart your softcam. If you leave it out, the plugin tries the
  common commands.

A backup `SoftCam.Key.bak` is written before every save.

## How the hash is calculated

CAID 2600 hash = CRC32 (seed 0x2600) over SID + namespace (the namespace is OR'd with
`0xA0000000`; when its lower 16 bits are zero, TSID and ONID are included too).
