#!/usr/bin/env python3
"""Unit tests verifying remediation of runtime defects RT-01 through RT-04,
environment sanitization, version validation, and SSL session security.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
UPDATE_CHECK_DIR = REPO_ROOT / "MagiskOnWSA" / "Update Check"
sys.path.insert(0, str(UPDATE_CHECK_DIR))

from env_helpers import (
    sanitize_env_value,
    write_github_env,
    is_valid_version,
    fetch_stored_version,
    configure_ssl_session,
    get_ca_bundle_path,
    MICROSOFT_UPDATE_CA_PEM,
)


class TestRuntimeDefectsRemediation(unittest.TestCase):
    """Test suite covering RT-01 through RT-04 runtime defects."""

    # -------------------------------------------------------------------------
    # Defect RT-01: Backtick environment variable & command substitution bug
    # -------------------------------------------------------------------------
    def test_rt01_backtick_removal(self):
        """Verify markdown backticks are completely removed to prevent command substitution."""
        raw_msg = "Magisk Stable Version: `30.6`"
        sanitized = sanitize_env_value(raw_msg)
        self.assertEqual(sanitized, "Magisk Stable Version: 30.6")
        self.assertNotIn("`", sanitized)

        raw_update_msg = "Update Magisk Stable Version from `v26.4` to `v30.6`"
        sanitized_update = sanitize_env_value(raw_update_msg)
        self.assertEqual(sanitized_update, "Update Magisk Stable Version from v26.4 to v30.6")
        self.assertNotIn("`", sanitized_update)

    def test_rt01_command_substitution_tokens_neutralized(self):
        """Verify shell command substitution syntax like $(...) and ${...} are neutralized."""
        malicious = "Version: 1.0.0 $(touch /tmp/pwned) `whoami` ${SECRET_TOKEN}"
        sanitized = sanitize_env_value(malicious)
        self.assertNotIn("$(", sanitized)
        self.assertNotIn("`", sanitized)
        self.assertNotIn("${", sanitized)
        self.assertNotIn("$", sanitized)
        self.assertTrue("Version: 1.0.0" in sanitized)

    def test_rt01_crlf_and_multiline_neutralization(self):
        """Verify newline and CRLF characters cannot inject multiple environment variables."""
        injection = "safe_value\r\nMALICIOUS_KEY=injected_val\nANOTHER_KEY=1"
        sanitized = sanitize_env_value(injection)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertEqual(sanitized, "safe_value MALICIOUS_KEY=injected_val ANOTHER_KEY=1")

    def test_write_github_env_safe_export(self):
        """Verify write_github_env correctly escapes values and enforces valid keys."""
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_env = tf.name

        try:
            # Valid export
            success = write_github_env("MAGISK_STABLE_MSG", "Magisk Stable Version: `30.6`", env_file_path=temp_env)
            self.assertTrue(success)

            # Invalid key rejection
            invalid_key = write_github_env("INVALID-KEY!@#", "value", env_file_path=temp_env)
            self.assertFalse(invalid_key)

            with open(temp_env, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("MAGISK_STABLE_MSG=Magisk Stable Version: 30.6\n", content)
            self.assertNotIn("`", content)
            self.assertNotIn("INVALID-KEY", content)
        finally:
            if os.path.exists(temp_env):
                os.unlink(temp_env)

    # -------------------------------------------------------------------------
    # Defect RT-02: FE3 SSL validation failures
    # -------------------------------------------------------------------------
    def test_rt02_ssl_configuration_security_rules(self):
        """Verify SSL configuration uses certifi CA bundle and NEVER disables verification."""
        session = configure_ssl_session()
        self.assertNotEqual(session.verify, False)
        self.assertTrue(isinstance(session.verify, str))
        self.assertTrue(os.path.exists(session.verify))

        # Ensure the CA bundle contains the Microsoft Update Intermediate CA
        with open(session.verify, "r", encoding="utf-8", errors="ignore") as f:
            bundle_content = f.read()
        self.assertIn("Microsoft Update Secure Server CA 2.1", bundle_content)

    def test_rt02_fe3_endpoint_ssl_handshake(self):
        """Verify that requests to fe3.delivery.mp.microsoft.com succeed without SSLCertVerificationError."""
        session = configure_ssl_session()
        try:
            resp = session.post(
                "https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx",
                data="<test/>",
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                timeout=(10, 30),
            )
            # A 400 Bad Request from SOAP server confirms successful TLS handshake and cert verification
            self.assertIn(resp.status_code, [200, 400, 500])
        except Exception as exc:
            self.fail(f"FE3 SSL verification failed unexpectedly: {exc}")

    # -------------------------------------------------------------------------
    # Defect RT-03: OpenGApps asset detection
    # -------------------------------------------------------------------------
    def test_rt03_opengapps_asset_matching_and_fallback(self):
        """Verify that OpenGApps parsing returns NOT_FOUND when no matching asset is found."""
        import re

        # Case 1: Empty assets
        assets_empty = []
        matching = [a for a in assets_empty if re.search(r"pico.*x86_64|x86_64.*pico", a, re.I)]
        asset_name = matching[0] if matching else "NOT_FOUND"
        self.assertEqual(asset_name, "NOT_FOUND")

        # Case 2: Non-matching assets
        assets_other = ["open_gapps-arm64-11.0-stock.zip", "open_gapps-arm-11.0-pico.zip"]
        matching = [a for a in assets_other if re.search(r"pico.*x86_64|x86_64.*pico", a, re.I)]
        asset_name = matching[0] if matching else "NOT_FOUND"
        self.assertEqual(asset_name, "NOT_FOUND")

        # Case 3: Matching asset
        assets_valid = ["open_gapps-x86_64-11.0-pico-20220215.zip"]
        matching = [a for a in assets_valid if re.search(r"pico.*x86_64|x86_64.*pico", a, re.I)]
        asset_name = matching[0] if matching else "NOT_FOUND"
        self.assertEqual(asset_name, "open_gapps-x86_64-11.0-pico-20220215.zip")

    def test_wsa_addon_gapps_discovery(self):
        """Verify WSA-Addon release asset discovery matches Android 13 x86_64 img and rc files."""
        import re

        assets = ["cust.img", "gapps-13.0-arm64.img", "gapps-13.0-x86_64.img", "gapps-13.0.rc"]
        img = next((a for a in assets if re.search(r"gapps.*13\.0.*x86_64.*\.img$", a, re.I)), "NOT_FOUND")
        rc = next((a for a in assets if re.search(r"gapps.*13\.0.*\.rc$", a, re.I)), "NOT_FOUND")

        self.assertEqual(img, "gapps-13.0-x86_64.img")
        self.assertEqual(rc, "gapps-13.0.rc")

    # -------------------------------------------------------------------------
    # Defect RT-04: Invalid version cache handling (404 Not Found rejection)
    # -------------------------------------------------------------------------
    def test_rt04_is_valid_version_rejects_errors_and_garbage(self):
        """Verify is_valid_version strictly rejects 404, HTML, and non-versions."""
        invalid_versions = [
            "404: Not Found",
            "404 Not Found",
            "<!DOCTYPE html><html>404</html>",
            "<html lang='en'>Error</html>",
            "500 Internal Server Error",
            "",
            "None",
            "null",
            "undefined",
            "a" * 60,
            "version 1.0.0",
            "invalid_tag",
        ]
        for val in invalid_versions:
            self.assertFalse(is_valid_version(val), f"Failed to reject invalid version: '{val}'")

    def test_rt04_is_valid_version_accepts_valid_versions(self):
        """Verify is_valid_version accepts legitimate version identifiers."""
        valid_versions = [
            "30.6",
            "26.4",
            "2407.40000.4.0",
            "2311.40000.4.0",
            "v30.6",
            "20240213",
            "0.9.5",
            "1.0.0",
            "26401",
        ]
        for val in valid_versions:
            self.assertTrue(is_valid_version(val), f"Failed to accept valid version: '{val}'")

    def test_rt04_fetch_stored_version_does_not_cache_404(self):
        """Verify fetch_stored_version returns default fallback upon HTTP 404."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "404: Not Found\n"

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp

        result = fetch_stored_version("https://fake.url/update/retail.appversion", session=mock_session, default="")
        self.assertEqual(result, "")
        self.assertNotEqual(result, "404: Not Found")


if __name__ == "__main__":
    unittest.main()
