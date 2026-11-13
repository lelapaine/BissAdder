# -*- coding: utf-8 -*-
# Reading / writing the SoftCam.Key file and restarting the softcam.
# Works on Python 2 and Python 3.
import os
import shlex
import subprocess

CONF_FILE = "/etc/tuxbox/config/BissAdder.conf"
DEFAULT_KEY_FILE = "/etc/tuxbox/config/SoftCam.Key"

# Folders checked (in this order) when key_file is not set in the config.
# File names are matched ignoring upper/lower case.
SEARCH_DIRS = [
    "/etc/tuxbox/config",
    "/etc/tuxbox/config/oscam",
    "/etc/tuxbox/config/ncam",
    "/usr/keys",
    "/var/keys",
    "/usr/local/keys",
    "/var/tuxbox/config",
    "/etc",
]
KEY_NAME = "softcam.key"

RESTART_COMMANDS = [
    ["/etc/init.d/softcam", "restart"],
    ["/etc/init.d/oscam", "restart"],
    ["/etc/init.d/ncam", "restart"],
    ["systemctl", "restart", "oscam"],
    ["systemctl", "restart", "ncam"],
    ["service", "oscam", "restart"],
    ["/etc/init.d/camd", "restart"],
    ["/usr/bin/restartcam"],
]


def read_config():
    """Read BissAdder.conf -> dict of key = value (empty dict if no file)."""
    conf = {}
    try:
        if not os.path.isfile(CONF_FILE):
            return conf
        f = open(CONF_FILE, "r")
        try:
            for line in f.read().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                conf[k.strip().lower()] = v.strip().strip('"').strip("'")
        finally:
            f.close()
    except (IOError, OSError):
        pass
    return conf


def _detect():
    for d in SEARCH_DIRS:
        try:
            if not os.path.isdir(d):
                continue
            for name in sorted(os.listdir(d)):
                if name.lower() == KEY_NAME and os.path.isfile(os.path.join(d, name)):
                    return os.path.join(d, name)
        except (IOError, OSError):
            continue
    return None


def get_key_file():
    """Config value first, then auto-detect, then the default path."""
    path = read_config().get("key_file")
    if path:
        return path
    return _detect() or DEFAULT_KEY_FILE


def _read_lines(path):
    if not os.path.isfile(path):
        return []
    f = open(path, "r")
    try:
        return f.read().splitlines()
    finally:
        f.close()


def read_keys(hashcode, path=None):
    """Return (key00, key01) already stored for this hash ('' if none)."""
    path = path or get_key_file()
    found = {"00": "", "01": ""}
    prefix = "F " + hashcode.upper() + " "
    for line in _read_lines(path):
        up = line.strip().upper()
        if up.startswith(prefix):
            parts = up.split()
            if len(parts) >= 4 and parts[2] in found:
                found[parts[2]] = parts[3]
    return found["00"], found["01"]


def save_keys(hashcode, key00, key01, path=None):
    """Replace/add the F lines for this hash. key01 may be '' (line skipped)."""
    path = path or get_key_file()
    hashcode = hashcode.upper()
    prefix = "F " + hashcode + " "
    old = _read_lines(path)
    kept = []
    for line in old:
        up = line.strip().upper()
        if up.startswith(prefix) and len(up.split()) >= 3 and up.split()[2] in ("00", "01"):
            continue  # drop old lines of this hash
        kept.append(line)
    while kept and not kept[-1].strip():
        kept.pop()
    kept.append("F %s 00 %s" % (hashcode, key00.upper()))
    if key01:
        kept.append("F %s 01 %s" % (hashcode, key01.upper()))
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    if os.path.isfile(path):
        try:
            bak = open(path + ".bak", "w")
            bak.write("\n".join(old) + "\n")
            bak.close()
        except (IOError, OSError):
            pass
    tmp = path + ".tmp"
    f = open(tmp, "w")
    try:
        f.write("\n".join(kept) + "\n")
        f.flush()
        os.fsync(f.fileno())
    finally:
        f.close()
    os.rename(tmp, path)
    return path


def _run(cmd):
    devnull = open(os.devnull, "w")
    try:
        return subprocess.call(cmd, stdout=devnull, stderr=subprocess.STDOUT)
    finally:
        devnull.close()


def restart_softcam():
    """Config restart_cmd first, then the common commands. Returns the command used or None."""
    candidates = []
    custom = read_config().get("restart_cmd")
    if custom:
        try:
            candidates.append(shlex.split(custom))
        except ValueError:
            pass
    candidates.extend(RESTART_COMMANDS)
    for cmd in candidates:
        try:
            if "/" in cmd[0] and not os.path.exists(cmd[0]):
                continue
            if _run(cmd) == 0:
                return " ".join(cmd)
        except (OSError, IOError):
            continue
    return None
