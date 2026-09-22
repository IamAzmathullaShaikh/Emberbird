"""PH-24 contract tests for the SLSA v0.2 build attestation generator.

Zero-mock law for provenance: a statement that claims more than the pipeline
can verify is worse than no statement. These tests pin the honesty flags
(``reproducible`` / ``completeness.environment`` must stay ``False`` until
real proofs exist), the digest-vs-disk verification, and the failure modes
(missing artifact, truncated commit, tampered subject).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "generate_attestation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_attestation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_attestation"] = module
    spec.loader.exec_module(module)
    return module


class TestStatementShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.artifact = Path(cls.tmp.name) / "Emberbird_WSA_TEST_x64.7z"
        cls.artifact.write_bytes(b"fixture artifact bytes")
        cls.statement = cls.mod.build_statement(cls.artifact, "TEST_TAG")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_in_toto_envelope_with_slsa_predicate(self):
        self.assertEqual(self.statement["_type"], "https://in-toto.io/Statement/v0.1")
        self.assertEqual(
            self.statement["predicateType"], "https://slsa.dev/provenance/v0.2"
        )

    def test_subject_digest_matches_artifact_bytes(self):
        expected = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.assertEqual(self.statement["subject"][0]["digest"]["sha256"], expected)
        self.assertEqual(self.statement["subject"][0]["name"], self.artifact.name)

    def test_config_source_carries_the_full_head_commit(self):
        commit = self.statement["predicate"]["invocation"]["configSource"]["digest"][
            "gitCommit"
        ]
        self.assertRegex(commit, r"^[0-9a-f]{40}$")

    def test_materials_include_the_pinned_cargo_lock(self):
        uris = [m["uri"] for m in self.statement["predicate"]["materials"]]
        self.assertTrue(
            any(u.endswith("Cargo.lock") for u in uris),
            f"materials must include the Cargo.lock, got: {uris}",
        )
        lock = ROOT / "apps/manager/src-tauri/Cargo.lock"
        digest = next(
            m["digest"]["sha256"]
            for m in self.statement["predicate"]["materials"]
            if m["uri"].endswith("Cargo.lock")
        )
        self.assertEqual(digest, hashlib.sha256(lock.read_bytes()).hexdigest())

    def test_honesty_flags_are_false_until_proven(self):
        metadata = self.statement["predicate"]["metadata"]
        self.assertFalse(
            metadata["reproducible"],
            "reproducible must not be claimed without a rebuild-and-compare proof",
        )
        self.assertFalse(
            metadata["completeness"]["environment"],
            "environment completeness must not be claimed while the toolchain is unpinned",
        )
        self.assertTrue(
            metadata["completeness"]["parameters"],
            "parameters ARE recorded and must be claimed",
        )

    def test_entry_point_names_the_real_assembly_script(self):
        entry = self.statement["predicate"]["invocation"]["configSource"]["entryPoint"]
        self.assertTrue((ROOT / entry).is_file(), f"entryPoint must exist: {entry}")


class TestValidationAndFailureModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.artifact = Path(cls.tmpdir.name) / "artifact.7z"
        cls.artifact.write_bytes(b"payload")

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_valid_statement_validates_clean(self):
        stmt = self.mod.build_statement(self.artifact, "T")
        self.assertEqual(self.mod.validate_statement(stmt, self.artifact), [])

    def test_tampered_subject_digest_is_caught(self):
        stmt = self.mod.build_statement(self.artifact, "T")
        stmt["subject"][0]["digest"]["sha256"] = "0" * 64
        errors = self.mod.validate_statement(stmt, self.artifact)
        self.assertTrue(any("does not match" in e for e in errors))

    def test_truncated_commit_is_caught(self):
        stmt = self.mod.build_statement(self.artifact, "T")
        stmt["predicate"]["invocation"]["configSource"]["digest"]["gitCommit"] = "abc123"
        errors = self.mod.validate_statement(stmt, self.artifact)
        self.assertTrue(any("full git SHA" in e for e in errors))

    def test_flipped_reproducible_flag_is_caught(self):
        """The honesty flags are themselves guarded: a future edit that flips
        them without adding the underlying proof fails the contract."""
        stmt = self.mod.build_statement(self.artifact, "T")
        stmt["predicate"]["metadata"]["reproducible"] = True
        errors = self.mod.validate_statement(stmt, self.artifact)
        self.assertTrue(any("reproducible" in e for e in errors))
        stmt2 = self.mod.build_statement(self.artifact, "T")
        stmt2["predicate"]["metadata"]["completeness"]["environment"] = True
        errors2 = self.mod.validate_statement(stmt2, self.artifact)
        self.assertTrue(any("environment" in e for e in errors2))

    def test_missing_artifact_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.mod.build_statement(self.artifact.parent / "ghost.7z", "T")

    def test_commit_override_must_be_a_full_sha(self):
        from unittest import mock
        with mock.patch.dict("os.environ", {"EMBERBIRD_SOURCE_COMMIT": "deadbeef"}):
            with self.assertRaises(ValueError):
                self.mod.build_statement(self.artifact, "T")

    def test_write_attestations_roundtrip(self):
        out = self.mod.write_attestations(self.artifact.parent, [self.artifact], "T")
        written = out / f"{self.artifact.name}.prov.json"
        self.assertTrue(written.is_file())
        stmt = json.loads(written.read_text(encoding="utf-8"))
        self.assertEqual(self.mod.validate_statement(stmt, self.artifact), [])


if __name__ == "__main__":
    unittest.main()
