"""RDB file constants and utilities."""

import base64

# Empty RDB file in base64 format
# This represents an empty Redis database snapshot
EMPTY_RDB_BASE64 = "UkVESVMwMDEx+glyZWRpcy12ZXIFNy4yLjD6CnJlZGlzLWJpdHPAQPoFY3RpbWXCbQi8ZfoIdXNlZC1tZW3CsMQQAPoIYW9mLWJhc2XAAP/wbjv+wP9aog=="

EMPTY_RDB = base64.b64decode(EMPTY_RDB_BASE64)

EMPTY_RDB_LENGTH = len(EMPTY_RDB)
