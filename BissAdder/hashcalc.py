# -*- coding: utf-8 -*-
# Hash calculation for BISS (CAID 2600). Works on Python 2 and Python 3.
import binascii

_TABLE = []
for _n in range(256):
    _c = _n
    for _k in range(8):
        if _c & 1:
            _c = 0xEDB88320 ^ (_c >> 1)
        else:
            _c = _c >> 1
    _TABLE.append(_c & 0xFFFFFFFF)


def crc32_2600(data):
    """CRC32 seeded with 0x2600 (same as the BISS key editor plugin)."""
    v = (0x2600 ^ 0xFFFFFFFF) & 0xFFFFFFFF
    for ch in bytearray(data):
        v = (_TABLE[(ch ^ v) & 0xFF] ^ (v >> 8)) & 0xFFFFFFFF
    return (v ^ 0xFFFFFFFF) & 0xFFFFFFFF


def parse_sref(text):
    """Return dict(sid, tsid, onid, ns) from '1:0:19:7:0:FF00:822A57:0:0:0:' or None."""
    try:
        parts = str(text).strip().split(":")
        if len(parts) < 7:
            return None
        return {
            "sid": int(parts[3], 16),
            "tsid": int(parts[4], 16),
            "onid": int(parts[5], 16),
            "ns": int(parts[6], 16),
        }
    except (ValueError, TypeError):
        return None


def biss_hash(sid, tsid, onid, ns):
    """Return the 8-character hash string for a service."""
    ns = (ns | 0xA0000000) & 0xFFFFFFFF
    if (ns & 0xFFFF) == 0:
        data = "%04X%04X%04X%08X" % (sid, tsid, onid, ns)
    else:
        data = "%04X%08X" % (sid, ns)
    return "%08X" % crc32_2600(binascii.unhexlify(data.encode("ascii")))


def hash_from_sref(sref):
    r = parse_sref(sref)
    if r is None:
        return None
    return biss_hash(r["sid"], r["tsid"], r["onid"], r["ns"])
