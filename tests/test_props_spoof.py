import io
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools/core/ to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "tools" / "core"
sys.path.insert(0, str(SCRIPT_DIR))

from fixGappsProp import Prop, _description, _fingerprint, _fix_prop


class TestFixGappsProp(unittest.TestCase):
    def test_prop_parsing_and_serialization(self):
        raw_prop = """# Comment line 1
ro.product.brand=Microsoft
ro.product.name=Subsystem
# Comment line 2

ro.build.version.release=13
"""
        p = Prop(io.StringIO(raw_prop))
        self.assertEqual(p.get_safe("ro.product.brand"), "Microsoft")
        self.assertEqual(p.get_safe("ro.product.name"), "Subsystem")
        self.assertEqual(p.get_safe("nonexistent_key", "default_val"), "default_val")

        serialized = str(p)
        self.assertIn("ro.product.brand=Microsoft", serialized)
        self.assertIn("# Comment line 1", serialized)

    def test_fix_prop_pixel5_spoofing(self):
        sample_prop = """# Stock WSA build.prop
ro.system.build.flavor=aosp_x86_64-user
ro.system.build.version.release_or_codename=13
ro.system.build.id=TQ3A.230901.001
ro.system.build.version.incremental=10750766
ro.system.build.type=user
ro.system.build.tags=release-keys
ro.system.build.version.release=13
ro.product.system.brand=Microsoft
ro.product.system.name=WindowsSubsystemForAndroid
ro.product.system.device=windows_x86_64
ro.product.system.model=Subsystem
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prop_file = Path(tmpdir) / "build.prop"
            prop_file.write_text(sample_prop, encoding="utf-8")

            _fix_prop(
                section="system",
                prop_path=str(prop_file),
                device_name="redfin",
                device_model="Pixel 5",
                gapps_variant="pico",
            )

            patched_content = prop_file.read_text(encoding="utf-8")
            patched_prop = Prop(io.StringIO(patched_content))

            # Verify spoofed attributes
            self.assertEqual(patched_prop.get_safe("ro.product.system.brand"), "google")
            self.assertEqual(patched_prop.get_safe("ro.product.system.manufacturer"), "Google")
            self.assertEqual(patched_prop.get_safe("ro.product.system.name"), "redfin")
            self.assertEqual(patched_prop.get_safe("ro.product.system.device"), "redfin")
            self.assertEqual(patched_prop.get_safe("ro.product.system.model"), "Pixel 5")
            self.assertIn("redfin", patched_prop.get_safe("ro.system.build.fingerprint"))


if __name__ == "__main__":
    unittest.main()
