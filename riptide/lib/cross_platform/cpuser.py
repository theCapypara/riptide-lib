"""
'Cross-platform' uid/gid retreival.
TODO: It's not actually cross-plarform. Under Windows it just returns 0 (root; default mapping for volumes).
"""
import os

FALLBACK_ID = 0


def getuid():
    try:
        return os.getuid()
    except AttributeError:
        return FALLBACK_ID


def getgid():
    try:
        return os.getgid()
    except AttributeError:
        return FALLBACK_ID
