#!/usr/bin/env python
"""Script to seed the database from Cloud Run."""

import subprocess
import sys

# 直接執行 seed_data.py
result = subprocess.run(
    [sys.executable, "seed_data.py"], capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr, file=sys.stderr)
sys.exit(result.returncode)
