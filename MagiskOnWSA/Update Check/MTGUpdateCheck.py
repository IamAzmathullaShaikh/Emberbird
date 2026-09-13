#!/usr/bin/python3
"""Check whether a newer MindTheGapps release is available and update the
gapps.appversion file + GITHUB_ENV message.

Note: this tracks the upstream MindTheGapps version for release notes. The
build itself consumes the WSA-Addon .img/.rc artifacts
(see scripts/generateGappsLink.py), so the two sources are intentionally
separate; GAPPS_ADDON_TAG in the build env records the exact addon release
that was used.
"""

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
url = f"https://raw.githubusercontent.com/{repo}/update/gapps.appversion"
currentver = fetch_stored_version(url, session=session, default="")

if not is_valid_version(currentver):
    print(f"Stored version '{currentver[:40]}' is not a valid version, bootstrapping from latest.")
    currentver = ""

if is_valid_version(currentver):
    with open('gapps.appversion', 'w', encoding='utf-8') as file:
        file.write(currentver)

try:
    headers = {"User-Agent": "WSABuilds-UpdateChecker"}
    token = os.getenv('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    resp = session.get(
        "https://api.github.com/repos/MustardChef/MindTheGappsArchived/releases/latest",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    latestver = str(json.loads(resp.content)['name']).strip().replace('\n', '')
except Exception as exc:
    print(f"Failed to fetch latest MindTheGapps version: {exc}")
    sys.exit(1)

if not is_valid_version(latestver):
    print(f"Invalid latest MindTheGapps version fetched: '{latestver}'")
    sys.exit(1)

if currentver != latestver:
    print(f"New version found: {latestver}")
    shell_exec = '/bin/bash' if os.path.exists('/bin/bash') else None
    subprocess.Popen(git, shell=True, stdout=None, stderr=None, executable=shell_exec).wait()
    with open('gapps.appversion', 'w', encoding='utf-8') as file:
        file.write(latestver)
    if currentver:
        mtgmsg = f"Update MindTheGapps Version from v{currentver} to v{latestver}"
    else:
        mtgmsg = f"MindTheGapps Package Version: {latestver}"
else:
    if not os.path.exists('gapps.appversion') or os.path.getsize('gapps.appversion') == 0:
        with open('gapps.appversion', 'w', encoding='utf-8') as file:
            file.write(latestver)
    mtgmsg = f"MindTheGapps Package Version: {latestver}"

print(f"MindTheGapps Version status: {mtgmsg}")
write_github_env("MTG_MSG", mtgmsg)
write_github_env("MTG_VER", latestver)
