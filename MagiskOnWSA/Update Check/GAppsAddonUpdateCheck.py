#!/usr/bin/python3
"""Check whether a newer WSA-Addon GApps release is available and update the
gappsaddon.appversion file + GITHUB_ENV message.

This tracks the upstream LSPosed/WSA-Addon repository, which supplies the
prebuilt GApps ext4 images (gapps-13.0-x86_64.img) and initrd mount scripts
(gapps-13.0.rc) consumed by scripts/generateGappsLink.py and build.sh.
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

# Ensure directory is in sys.path for importing env_helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_helpers import (
    configure_ssl_session,
    fetch_stored_version,
    is_valid_version,
    sanitize_env_value,
    write_github_env,
)

logging.captureWarnings(True)
session = configure_ssl_session()

# Create the update branch from the current HEAD instead of discarding the
# whole working tree with an orphan branch when the branch does not exist yet.
git = (
    "git checkout -f update 2>/dev/null || git checkout -b update"
)

repo = os.getenv('GITHUB_REPOSITORY', 'MustardChef/WSABuilds')
url = f"https://raw.githubusercontent.com/{repo}/update/gappsaddon.appversion"
currentver = fetch_stored_version(url, session=session, default="")

if not is_valid_version(currentver):
    print(f"Stored version '{currentver[:40]}' is not a valid version, bootstrapping from latest.")
    currentver = ""

if is_valid_version(currentver):
    with open('gappsaddon.appversion', 'w', encoding='utf-8') as file:
        file.write(currentver)

owner = "LSPosed"
repo_name = "WSA-Addon"
api_url = f"https://api.github.com/repos/{owner}/{repo_name}/releases/latest"
headers = {"User-Agent": "WSABuilds-UpdateChecker"}
token = os.getenv('GITHUB_TOKEN')
if token:
    headers['Authorization'] = f'Bearer {token}'

try:
    resp = session.get(api_url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = json.loads(resp.content)
    latestver = str(data.get('tag_name', 'v2')).strip()
    assets = [a.get('name', '') for a in data.get('assets', [])]
except Exception as exc:
    print(f"Failed to fetch latest WSA-Addon release: {exc}")
    sys.exit(1)

if not is_valid_version(latestver):
    print(f"Invalid latest WSA-Addon version fetched: '{latestver}'")
    sys.exit(1)

# Verify required Android 13 x86_64 image and rc assets exist
img_asset = next((a for a in assets if re.search(r"gapps.*13\.0.*x86_64.*\.img$", a, re.I)), "NOT_FOUND")
rc_asset = next((a for a in assets if re.search(r"gapps.*13\.0.*\.rc$", a, re.I)), "NOT_FOUND")

if img_asset == "NOT_FOUND" or rc_asset == "NOT_FOUND":
    print(f"[-] Warning: WSA-Addon release {latestver} does not contain complete Android 13 x86_64 assets. Found: {assets}")

if currentver != latestver:
    print(f"New WSA-Addon version found: {latestver}")
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        shell_exec = '/bin/bash' if os.path.exists('/bin/bash') else None
        subprocess.Popen(git, shell=True, stdout=None, stderr=None, executable=shell_exec).wait()
    with open('gappsaddon.appversion', 'w', encoding='utf-8') as file:
        file.write(latestver)
    if currentver:
        gapps_msg = f"Update GApps (WSA-Addon) Version from {currentver} to {latestver}"
    else:
        gapps_msg = f"GApps (WSA-Addon) Version: {latestver}"
else:
    if not os.path.exists('gappsaddon.appversion') or os.path.getsize('gappsaddon.appversion') == 0:
        with open('gappsaddon.appversion', 'w', encoding='utf-8') as file:
            file.write(latestver)
    gapps_msg = f"GApps (WSA-Addon) Version: {latestver}"

print(f"GApps Version status: {gapps_msg}")
print(f"GApps Asset: {img_asset}")
print(f"GApps RC: {rc_asset}")

write_github_env("GAPPS_TAG", latestver)
write_github_env("GAPPS_ASSET", img_asset)
write_github_env("GAPPS_RC", rc_asset)
write_github_env("GAPPS_MSG", gapps_msg)
write_github_env("GAPPS_VARIANT", "Pico (WSA-Addon)")
