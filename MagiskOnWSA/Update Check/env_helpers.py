#!/usr/bin/env python3
"""Central helper functions for WSA update checks:
- Safe environment value escaping and export to GITHUB_ENV
- Strict version string validation rejecting 404/HTML responses
- Resilient SSL session configuration using certifi CA store (strictly verify=True)
"""

import os
import re
import certifi
import requests
from typing import Any, Optional
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from packaging import version


def sanitize_env_value(value: Any) -> str:
    """Sanitize an environment value before writing to GITHUB_ENV or shell commands.

    - Removes markdown backticks (`` ` ``) to prevent shell command substitution
    - Removes dollar signs ($) and command expansion constructs ($(), ${})
    - Strips carriage returns and converts newlines to spaces to prevent line injection
    - Strips leading and trailing whitespace
    """
    if value is None:
        return ""
    val_str = str(value)
    # Strip backticks
    val_str = val_str.replace("`", "")
    # Remove command substitution syntax $(...) and variable interpolation ${...}
    val_str = re.sub(r"\$\([^\)]*\)", "", val_str)
    val_str = re.sub(r"\$\{[^\}]*\}", "", val_str)
    # Remove raw dollar signs
    val_str = val_str.replace("$", "")
    # Prevent multiline / CRLF header or environment injection
    val_str = val_str.replace("\r", "").replace("\n", " ").strip()
    return val_str


def write_github_env(key: str, value: Any, env_file_path: Optional[str] = None) -> bool:
    """Safely append a sanitized KEY=VALUE pair to GITHUB_ENV.

    Validates that the key is a legal identifier and the value is sanitized.
    """
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        print(f"[-] Invalid environment variable key rejected: '{key}'")
        return False

    target_file = env_file_path or os.getenv("GITHUB_ENV")
    if not target_file:
        return False

    sanitized_val = sanitize_env_value(value)
    try:
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={sanitized_val}\n")
        return True
    except Exception as exc:
        print(f"[-] Failed writing {key} to GITHUB_ENV ({target_file}): {exc}")
        return False


def is_valid_version(val: Any) -> bool:
    """Strictly validate whether a string represents a valid version identifier.

    Rejects:
    - 404 responses ("404: Not Found", etc.)
    - HTML error responses ("<!DOCTYPE html>", "<html>", etc.)
    - Non-version or malformed strings
    """
    if not val or not isinstance(val, str):
        return False

    clean = val.strip()
    if not clean or len(clean) > 50:
        return False

    lower = clean.lower()
    reject_tokens = ["404", "not found", "html", "<!doctype", "error", "forbidden", "unauthorized", "none", "null"]
    if any(token in lower for token in reject_tokens):
        return False

    # Standard version patterns: e.g. 30.6, 2311.40000.4.0, v30.6, 26401
    if not re.match(r"^v?\d+(\.\d+)*$", clean):
        return False

    try:
        version.parse(clean.lstrip("v"))
        return True
    except Exception:
        return False


def fetch_stored_version(
    url: str,
    session: Optional[requests.Session] = None,
    timeout: int = 30,
    default: str = "0",
) -> str:
    """Fetch stored version from a remote URL (e.g. raw.githubusercontent.com).

    Verifies HTTP 200 and strict version validity. If the file does not exist (404),
    is invalid, or network fails, returns `default` safely without caching garbage.
    """
    client = session or requests
    try:
        resp = client.get(url, timeout=timeout)
        if resp.status_code == 200:
            content = resp.text.strip().replace("\r", "").replace("\n", "")
            if is_valid_version(content):
                return content
            print(f"Stored version '{content[:40]}' is not a valid version, defaulting to '{default}'")
            return default
        else:
            print(f"HTTP {resp.status_code} fetching stored version from {url}, defaulting to '{default}'")
            return default
    except Exception as exc:
        print(f"Network error fetching stored version from {url}: {exc}, defaulting to '{default}'")
        return default


# Microsoft Update Secure Server CA 2.1 (intermediate CA required for fe3.delivery.mp.microsoft.com)
# Chained to "Microsoft Root Certificate Authority 2011" present in Mozilla / certifi root store.
# fe3.delivery.mp.microsoft.com omits this intermediate in its TLS handshake, causing OpenSSL
# to raise SSLCertVerificationError unless the intermediate is available in the local CA store.
MICROSOFT_UPDATE_CA_PEM = """
-----BEGIN CERTIFICATE-----
MIIHADCCBOigAwIBAgITMwAAAAq4kaLIClCl3wAAAAAACjANBgkqhkiG9w0BAQsF
ADCBiDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCldhc2hpbmd0b24xEDAOBgNVBAcT
B1JlZG1vbmQxHjAcBgNVBAoTFU1pY3Jvc29mdCBDb3Jwb3JhdGlvbjEyMDAGA1UE
AxMpTWljcm9zb2Z0IFJvb3QgQ2VydGlmaWNhdGUgQXV0aG9yaXR5IDIwMTEwHhcN
MTIwNjIxMTczMzM1WhcNMjcwNjIxMTc0MzM1WjCBhDELMAkGA1UEBhMCVVMxEzAR
BgNVBAgTCldhc2hpbmd0b24xEDAOBgNVBAcTB1JlZG1vbmQxHjAcBgNVBAoTFU1p
Y3Jvc29mdCBDb3Jwb3JhdGlvbjEuMCwGA1UEAxMlTWljcm9zb2Z0IFVwZGF0ZSBT
ZWN1cmUgU2VydmVyIENBIDIuMTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoC
ggIBAIsV6r17t2cxpIcOFIqSCXjB1Wi28ppZ4H/IGmdG3jGaAqrI50dJ6ak6h0yF
/jwuG0cERatWEbtguFI2idurX8gorvMbOaC/BqJk2azmI0PNaZWQ5a+Ib5jb+yLC
ByxI8UyFA1pqzUBh4SIaIuObKz3s44ubK8xVZYEUuszhiv7QvDonFzpHQfu4MPEE
MtHVOW56RssyKuFzdos1OhXYjpSCZni+kXwLowGugOMJhCxpK9mMJNTyPzUHd+Gf
41RDX+yK/SRYT6NUYNIAX3VEK9Lvf7s+tl77d/vhnmalQB8xPNDjMgS4p+ulEt9w
Gmrwo1IQuFjDiH2kszH5f2FTri3Mgjr2SotDZPLMk93g1RQuSAZmEED2I+efOVC4
dyESKUB7/Hf0MNNeujezZyA7ih3/mXg5ppuFz61acjBRKlmNKBc1MnqUHbBSBX9K
BuBNfeqW1SsMoy2JWrVcKqvEtqbTX2mfEEMA/aecmMO6S7vo2CM8c7OBFjY9sbxh
msAS3TC0kLffSK3YF2oDMqdgW57PGm14ZVSP01KO5W6E8sq43xkd2rT6KZ7IHqPW
18QwPsHbffy5eQbgumeadF3cryR7ElIt1VccANw9mqA+km1DWoL3tYb+nlS0MMKd
YNFPT903Vx0chN5ej9CQXHBu4zq3Rkmz7wF5YJVEO9gZ0CJlAgMBAAGjggFjMIIB
XzAQBgkrBgEEAYI3FQEEAwIBADAdBgNVHQ4EFgQU0vI9hHSGG1CFql3lpQea8EfT
LmkwGQYJKwYBBAGCNxQCBAweCgBTAHUAYgBDAEEwCwYDVR0PBAQDAgGGMBIGA1Ud
EwEB/wQIMAYBAf8CAQAwHwYDVR0jBBgwFoAUci06AjGQQ7kUBU7h6qfHMdEjiTQw
WgYDVR0fBFMwUTBPoE2gS4ZJaHR0cDovL2NybC5taWNyb3NvZnQuY29tL3BraS9j
cmwvcHJvZHVjdHMvTWljUm9vQ2VyQXV0MjAxMV8yMDExXzAzXzIyLmNybDBeBggr
BgEFBQcBAQRSMFAwTgYIKwYBBQUHMAKGQmh0dHA6Ly93d3cubWljcm9zb2Z0LmNv
bS9wa2kvY2VydHMvTWljUm9vQ2VyQXV0MjAxMV8yMDExXzAzXzIyLmNydDATBgNV
HSUEDDAKBggrBgEFBQcDATANBgkqhkiG9w0BAQsFAAOCAgEAopvuA2tH2+meSVsn
VatGbRha0QgVj4Saq5ZlNJW0Qpyf4pRyuZT+KLK2/Ia6ZzUugrtLAECro+hIEB5K
29S+pnY1nzSMn+lSZJwGWfRZTWn466g21wKFMInPpO3QB8yfzr2zwniissTh8Jkn
8Uejsz/EkGU520E3FCT26dlU1YtzHnrcZ7d8qp4tLFEVeSsrxkqpYJQxalJIZ3HH
uhOG3BQLmLtJDs822W1knAR6c+iYuLDbJ9o8TnOY9/lIWy8Vv2z3i+LEn27O7QSl
vTZHyCgFJMgjhELOSLliGhA3411RX8kyCE9AJ1OLufdcejOYwMG0POpmrj3s/Q5n
+Bfm5JQHaGGCUy7XfKMRbyYJejjcC1YtLS5HVxBf/Smh7nruCYIpDimr8AIgJCVz
ekbVxTHzuSYdXLZgnpUzu71MgFGSBh5DAHaErUmwwztK/TIyak9zwodWouV+2clp
HYgCWASmHOkRysH6T3n46pDmexplqG5dGM5QNrCjn5u1ptgVdDPR1LGHTT+KGT+F
45owrOFOwUOuz2H6RFUPgwPkCOYnK4bM17tdlaQ4DrtghSqL03ZaPFdASXHa+fZB
1ro0E6c8fv9vqaf7NvhIQE+BepDH87/f3gCGCzZ0pTNnbRH2k2VCc4CbaWZRKWg8
5c95ZPsdlHeynrIjVZ76ubrfiuM=
-----END CERTIFICATE-----
"""


def get_ca_bundle_path() -> str:
    """Return the absolute path to a comprehensive CA bundle containing certifi roots
    plus the Microsoft Update intermediate CA.
    """
    import tempfile
    bundle_path = os.path.join(tempfile.gettempdir(), "wsa_certifi_ca_bundle.pem")
    base_ca = certifi.where()

    # Recreate bundle if not exists or if source certifi file is newer
    if not os.path.exists(bundle_path) or os.path.getmtime(bundle_path) < os.path.getmtime(base_ca):
        try:
            with open(base_ca, "rb") as f_in:
                content = f_in.read()
            with open(bundle_path, "wb") as f_out:
                f_out.write(content)
                f_out.write(b"\n# Microsoft Update Secure Server CA 2.1 (AIA intermediate)\n")
                f_out.write(MICROSOFT_UPDATE_CA_PEM.strip().encode("utf-8"))
                f_out.write(b"\n")
        except Exception as exc:
            print(f"[-] Warning: Failed creating combined CA bundle ({exc}), falling back to default certifi.")
            return base_ca

    return bundle_path


def configure_ssl_session(
    session: Optional[requests.Session] = None,
    total_retries: int = 3,
    backoff_factor: float = 1.0,
) -> requests.Session:
    """Configure requests.Session with certifi CA bundle and robust retry adapter.

    Enforces strictly valid SSL transport (verify=certifi CA bundle) and handles
    transient network errors or gateway drops. Never disables verification.
    """
    sess = session or requests.Session()
    ca_bundle = get_ca_bundle_path()
    sess.verify = ca_bundle

    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    sess.headers.update({
        "User-Agent": "WSABuilds-UpdateChecker/1.0",
    })
    return sess

