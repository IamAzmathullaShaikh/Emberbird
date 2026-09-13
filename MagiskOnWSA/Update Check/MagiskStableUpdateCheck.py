#!/usr/bin/python3
"""Check whether a newer Magisk stable release is available and update the
magiskstable.appversion file + GITHUB_ENV message."""

import os
import sys
import json
import logging
import subprocess

# Ensure directory is in sys.path for importing env_helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_helpers import (
    is_valid_version,
    fetch_stored_version,
    write_github_env,
    configure_ssl_session,
    sanitize_env_value,
)

logging.captureWarnings(True)
session = configure_ssl_session()

# Create the update branch from the current HEAD instead of discarding the
# whole working tree with an orphan branch when the branch does not exist yet.
git = (
    "git checkout -f update 2>/dev/null || git checkout -b update"
)

repo = os.getenv('GITHUB_REPOSITORY', 'MustardChef/WSABuilds')
url = f"https://raw.githubusercontent.com/{repo}/update/magiskstable.appversion"
currentver = fetch_stored_version(url, session=session, default="")

if not is_valid_version(currentver):
    print(f"Stored version '{currentver[:40]}' is not a valid version, bootstrapping from latest.")
    currentver = ""

if is_valid_version(currentver):
    with open('magiskstable.appversion', 'w', encoding='utf-8') as file:
        file.write(currentver)

try:
    resp = session.get(
        "https://github.com/topjohnwu/magisk-files/raw/master/stable.json",
        timeout=30,
    )
    resp.raise_for_status()
    latestver = str(json.loads(resp.content)['magisk']['version']).strip().replace('\n', '')
except Exception as exc:
    print(f"Failed to fetch latest Magisk stable version: {exc}")
    sys.exit(1)

if not is_valid_version(latestver):
    print(f"Invalid latest Magisk version fetched: '{latestver}'")
    sys.exit(1)

if currentver != latestver:
    print(f"New version found: {latestver}")
    shell_exec = '/bin/bash' if os.path.exists('/bin/bash') else None
    subprocess.Popen(git, shell=True, stdout=None, stderr=None, executable=shell_exec).wait()
    with open('magiskstable.appversion', 'w', encoding='utf-8') as file:
        file.write(latestver)
    if currentver:
        magiskstablemsg = f"Update Magisk Stable Version from v{currentver} to v{latestver}"
    else:
        magiskstablemsg = f"Magisk Stable Version: {latestver}"
else:
    if not os.path.exists('magiskstable.appversion') or os.path.getsize('magiskstable.appversion') == 0:
        with open('magiskstable.appversion', 'w', encoding='utf-8') as file:
            file.write(latestver)
    magiskstablemsg = f"Magisk Stable Version: {latestver}"

print(f"Magisk Stable Version status: {magiskstablemsg}")
write_github_env("MAGISK_STABLE_MSG", magiskstablemsg)
write_github_env("MAGISK_STABLE_VER", latestver)
