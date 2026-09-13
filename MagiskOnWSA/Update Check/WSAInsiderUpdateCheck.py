#!/usr/bin/python3
"""Check for a newer Windows Subsystem for Android (Insider Fast / WIF) build
via Microsoft's FE3 delivery service and update the WIF.appversion file.

The FE3 XML request templates are read from the directory given in the
WSA_XML_DIR environment variable (GitHub runner layout independent), falling
back to the repo's own MagiskOnWSA/xml directory.
"""

import base64
import os
import html
import re
import sys
import logging
import subprocess

from typing import Any, OrderedDict
from xml.dom import minidom
from packaging import version

# Ensure directory is in sys.path for importing env_helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_helpers import (
    is_valid_version,
    fetch_stored_version,
    write_github_env,
    configure_ssl_session,
    sanitize_env_value,
)


class Prop(OrderedDict):
    def __init__(self, props: str = ...) -> None:
        super().__init__()
        for i, line in enumerate(props.splitlines(False)):
            if '=' in line:
                k, v = line.split('=', 1)
                self[k] = v
            else:
                self[f".{i}"] = line

    def __setattr__(self, __name: str, __value: Any) -> None:
        self[__name] = __value

    def __repr__(self):
        return '\n'.join(f'{item}={self[item]}' for item in self)


logging.captureWarnings(True)

# Category ID of the Windows Subsystem for Android feed
cat_id = '858014f3-3934-4abe-8078-4aa193e74ca8'

release_type = "WIF"

# Configure session with certifi CA store and retries (verify=certifi CA bundle with MS intermediate)
session = configure_ssl_session()

# Create the update branch from the current HEAD instead of discarding the
# whole working tree with an orphan branch when the branch does not exist yet.
git = (
    "git checkout -f update 2>/dev/null || git checkout -b update"
)

# Runner layout independent path to the FE3 XML request templates
xml_dir = os.environ.get(
    "WSA_XML_DIR",
    os.path.join(os.getcwd(), "MagiskOnWSA", "xml"),
)

# Fetch the Microsoft account user code (required to access the insider feed)
user_code = ""
try:
    response = session.get(
        "https://api.github.com/repos/bubbles-wow/MS-Account-Token/contents/token.cfg",
        timeout=30)
    if response.status_code == 200:
        content = base64.b64decode(
            response.json()["content"].encode("utf-8")).decode("utf-8")
        props = Prop(content)
        user_code = props.get("user_code") or ""
        print("Successfully got user token from server!")
        print(f"Last update time: {props.get('update_time')}\n")
    else:
        print(f"Failed to get user token from server! Error code: {response.status_code}\n")
except Exception as exc:
    print(f"Failed to get user token from server! {exc}\n")

repo = os.getenv('GITHUB_REPOSITORY', 'MustardChef/WSABuilds')
url = f"https://raw.githubusercontent.com/{repo}/update/WIF.appversion"
currentver = fetch_stored_version(url, session=session, default="")

if not is_valid_version(currentver):
    print(f"Stored version '{currentver[:40]}' is not a valid version, treating as none")
    currentver = ""
    current = version.parse("0")
else:
    current = version.parse(currentver)
    # Only write stored version if it is strictly valid
    try:
        with open('WIF.appversion', 'w', encoding='utf-8') as file:
            file.write(currentver)
        print("WIF.appversion file written.")
    except Exception as e:
        print(f"Error writing to file: {e}")


def query_fe3():
    """Return the newest WSA build version from FE3, or None on failure."""
    try:
        with open(os.path.join(xml_dir, "GetCookie.xml"), "r", encoding="utf-8") as f:
            cookie_content = f.read().format(user_code)
        out = session.post(
            'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
            data=cookie_content,
            headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
            timeout=(15, 60))
        doc = minidom.parseString(out.text)
        cookie = doc.getElementsByTagName('EncryptedData')[0].firstChild.nodeValue
        with open(os.path.join(xml_dir, "WUIDRequest.xml"), "r", encoding="utf-8") as f:
            cat_id_content = f.read().format(user_code, cookie, cat_id, release_type)
        out = session.post(
            'https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx',
            data=cat_id_content,
            headers={'Content-Type': 'application/soap+xml; charset=utf-8'},
            timeout=(15, 60))
        doc = minidom.parseString(html.unescape(out.text))
    except Exception as exc:
        print(f"Network/XML error while querying FE3: {exc}")
        print(f"SSL CA bundle in use: {session.verify}")
        return None

    filenames = {}
    for node in doc.getElementsByTagName('ExtendedUpdateInfo')[0].getElementsByTagName('Updates')[0].getElementsByTagName('Update'):
        node_xml = node.getElementsByTagName('Xml')[0]
        node_files = node_xml.getElementsByTagName('Files')
        if not node_files:
            continue
        for node_file in node_files[0].getElementsByTagName('File'):
            if node_file.hasAttribute('InstallerSpecificIdentifier') and node_file.hasAttribute('FileName'):
                filenames[node.getElementsByTagName('ID')[0].firstChild.nodeValue] = (
                    f"{node_file.attributes['InstallerSpecificIdentifier'].value}_{node_file.attributes['FileName'].value}",
                    node_xml.getElementsByTagName('ExtendedProperties')[0].attributes['PackageIdentityName'].value)

    identities = {}
    for node in doc.getElementsByTagName('NewUpdates')[0].getElementsByTagName('UpdateInfo'):
        node_xml = node.getElementsByTagName('Xml')[0]
        if not node_xml.getElementsByTagName('SecuredFragment'):
            continue
        id_ = node.getElementsByTagName('ID')[0].firstChild.nodeValue
        update_identity = node_xml.getElementsByTagName('UpdateIdentity')[0]
        if id_ in filenames:
            fileinfo = filenames[id_]
            if fileinfo[0] not in identities:
                identities[fileinfo[0]] = ([update_identity.attributes['UpdateID'].value,
                                            update_identity.attributes['RevisionNumber'].value], fileinfo[1])

    wsa_build_ver = 0
    for filename in identities:
        if re.match(r"MicrosoftCorporationII\.WindowsSubsystemForAndroid_.*\.msixbundle", filename):
            tmp = re.search(r"\d{4}\.\d{5}\.\d{1,}\.\d{1,}", filename)
            if not tmp:
                continue
            tmp_wsa_build_ver = tmp.group()
            if wsa_build_ver == 0:
                wsa_build_ver = tmp_wsa_build_ver
            elif version.parse(wsa_build_ver) < version.parse(tmp_wsa_build_ver):
                wsa_build_ver = tmp_wsa_build_ver
    return wsa_build_ver


wsa_build_ver = query_fe3()
if wsa_build_ver in (None, 0):
    print("No WSA version information could be retrieved, skipping update check.")
    write_github_env("WSA_UPDATE_STATUS", "UNAVAILABLE")
    write_github_env("INSIDER_UPDATE", "no")
    write_github_env("SHOULD_BUILD", "no")
    sys.exit(0)

try:
    latest = version.parse(str(wsa_build_ver))
except Exception:
    print(f"Invalid version returned by FE3: {wsa_build_ver}")
    write_github_env("WSA_UPDATE_STATUS", "UNAVAILABLE")
    write_github_env("INSIDER_UPDATE", "no")
    write_github_env("SHOULD_BUILD", "no")
    sys.exit(0)

if current < latest:
    print(f"New version found: {wsa_build_ver}")
    shell_exec = '/bin/bash' if os.path.exists('/bin/bash') else None
    subprocess.Popen(git, shell=True, stdout=None, stderr=None, executable=shell_exec).wait()
    try:
        with open('WIF.appversion', 'w', encoding='utf-8') as file:
            file.write(str(wsa_build_ver))
        print("WIF.appversion updated.")
    except Exception as e:
        print(f"Error writing to file: {e}")
    if currentver:
        msg = f'Update WSA Version from v{currentver} to v{wsa_build_ver}'
    else:
        msg = f'WSA Version: v{wsa_build_ver}'
    write_github_env("SHOULD_BUILD", "yes")
    write_github_env("RELEASE_TYPE", release_type)
    write_github_env("LATEST_WIF_VER", str(wsa_build_ver))
    write_github_env("MSG", msg)
    write_github_env("INSIDER_UPDATE", "yes")
    write_github_env("WSA_UPDATE_STATUS", "AVAILABLE")
else:
    print(f"WSA WIF version is up to date: {currentver}")
    if not os.path.exists('WIF.appversion') or os.path.getsize('WIF.appversion') == 0:
        with open('WIF.appversion', 'w', encoding='utf-8') as file:
            file.write(str(currentver if currentver else wsa_build_ver))
    write_github_env("WSA_UPDATE_STATUS", "NO_CHANGE")
    write_github_env("INSIDER_UPDATE", "no")
    write_github_env("SHOULD_BUILD", "no")
    write_github_env("LATEST_WIF_VER", str(currentver if currentver else wsa_build_ver))
