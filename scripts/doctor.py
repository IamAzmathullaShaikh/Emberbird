#!/usr/bin/env python3
"""scripts/doctor.py — Project Doctor Convenience CLI Entry Point."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATFORM_DIR = REPO_ROOT / "platform"
if str(PLATFORM_DIR) not in sys.path:
    sys.path.insert(0, str(PLATFORM_DIR))

from doctor.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
