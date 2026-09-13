import io
import lzma
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add MagiskOnWSA/scripts to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "MagiskOnWSA" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_local import CpioEntry, read_cpio_archive, write_cpio_archive, compress_xz


class TestCpioArchive(unittest.TestCase):
    def test_cpio_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test_initrd.cpio"

            sample_entries = [
                CpioEntry(name=".backup", data=b"", mode=0o40000, nlink=2),
                CpioEntry(name="init", data=b"lspinit", mode=0o120000),
                CpioEntry(name="lspinit", data=b"ELF_MOCK_LSPINIT_PAYLOAD", mode=0o100750),
                CpioEntry(name="wsainit", data=b"ELF_MOCK_WSAINIT_PAYLOAD_12345", mode=0o100777),
                CpioEntry(name="overlay.d", data=b"", mode=0o40750, nlink=2),
                CpioEntry(name="overlay.d/sbin/post-fs-data.sh", data=b"#!/bin/sh\necho hello\n", mode=0o100755),
            ]

            write_cpio_archive(archive_path, sample_entries)
            self.assertTrue(archive_path.exists())
            self.assertGreater(archive_path.stat().st_size, 0)

            # Read back archive
            read_entries = read_cpio_archive(archive_path)

            # The archive should contain the sample entries plus TRAILER!!!
            entry_names = [e.name for e in read_entries]
            self.assertIn(".backup", entry_names)
            self.assertIn("init", entry_names)
            self.assertIn("lspinit", entry_names)
            self.assertIn("wsainit", entry_names)
            self.assertIn("overlay.d/sbin/post-fs-data.sh", entry_names)
            self.assertIn("TRAILER!!!", entry_names)

            # Check specific entry payload and mode
            lspinit_e = next(e for e in read_entries if e.name == "lspinit")
            self.assertEqual(lspinit_e.data, b"ELF_MOCK_LSPINIT_PAYLOAD")
            self.assertEqual(lspinit_e.mode, 0o100750)

            post_fs_e = next(e for e in read_entries if e.name == "overlay.d/sbin/post-fs-data.sh")
            self.assertEqual(post_fs_e.data, b"#!/bin/sh\necho hello\n")
            self.assertEqual(post_fs_e.mode, 0o100755)

    def test_cpio_header_magic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "magic_check.cpio"
            write_cpio_archive(archive_path, [CpioEntry(name="test.txt", data=b"hello", mode=0o100644)])
            
            with open(archive_path, "rb") as f:
                header = f.read(6)
                self.assertEqual(header, b"070701", "CPIO archive must have SVR4 new ascii format magic 070701")

    def test_compress_xz_crc32(self):
        data = b"Arbitrary payload for XZ compression testing." * 50
        compressed = compress_xz(data)
        
        self.assertGreater(len(compressed), 0)
        self.assertLess(len(compressed), len(data))
        
        # Decompress and verify
        decompressed = lzma.decompress(compressed)
        self.assertEqual(decompressed, data)


if __name__ == "__main__":
    unittest.main()
