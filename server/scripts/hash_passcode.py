#!/usr/bin/env python3
"""Hash a passcode for PASSCODE_HASH in .env."""
import sys

from app.auth import hash_passcode

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/hash_passcode.py 'your passcode'", file=sys.stderr)
        sys.exit(1)
    print(hash_passcode(sys.argv[1]))
