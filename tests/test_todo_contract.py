#!/usr/bin/env python3
"""TODO.md contract tests (WO-4b, Cycle S1).

TODO.md is the single executable roadmap. These tests pin its binding
structure so the roadmap cannot silently decay:

- The Execution Contract must be present and complete.
- A phase may not claim COMPLETE while its exit checklist has unchecked
  items, unless the header explicitly annotates the pending item (e.g.
  CI ratification).
- Future phases must stay marked LOCKED.
- The execution-engine field vocabulary must exist.

stdlib-only; runs in CI unchanged.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TODO = REPO_ROOT / "TODO.md"

EXECUTION_CONTRACT_ITEMS = [
    "One active phase",
    "Phase guard",
    "Exit checklists",
    "Reality gates before merge",
    "Protected subsystems",
    "Status vocabulary",
    "Stop conditions",
    "Contracts frozen",
]

EXECUTION_ENGINE_FIELDS = ["STATUS", "BLOCKERS", "DEPENDENCIES", "FILES", "RISKS", "VALIDATION", "RESULT"]

PHASE_RE = re.compile(r"^### (.+)$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^- \[([ x!])\]", re.MULTILINE)


def todo_text() -> str:
    return TODO.read_text(encoding="utf-8")


class TestExecutionContract(unittest.TestCase):
    def test_todo_exists(self):
        self.assertTrue(TODO.is_file(), "TODO.md must exist — it is the single executable roadmap")

    def test_all_execution_contract_items_present(self):
        text = todo_text()
        missing = [item for item in EXECUTION_CONTRACT_ITEMS if item not in text]
        self.assertEqual(missing, [], f"Execution Contract items missing from TODO.md: {missing}")

    def test_execution_engine_fields_documented(self):
        text = todo_text()
        missing = [f for f in EXECUTION_ENGINE_FIELDS if f not in text]
        self.assertEqual(missing, [], f"execution-engine fields missing from TODO.md: {missing}")

    def test_truth_hierarchy_documented(self):
        text = todo_text().lower()
        for needle in ["l1", "published release assets", "reality always overrides documentation"]:
            self.assertIn(needle, text, f"truth-hierarchy element missing: {needle}")


class TestPhaseHonesty(unittest.TestCase):
    """A phase section claiming COMPLETE must not hide unchecked items."""

    def test_no_phase_claims_complete_with_silent_unchecked_items(self):
        text = todo_text()
        sections = PHASE_RE.split(text)
        # sections = [prefix, title1, body1, title2, body2, ...]
        problems = []
        for i in range(1, len(sections) - 1, 2):
            title, body = sections[i], sections[i + 1]
            unchecked = len(CHECKBOX_RE.findall(body))
            if unchecked and "complete" in title.lower() and "pending" not in title.lower():
                problems.append(f"phase '{title}' claims COMPLETE with {unchecked} unchecked item(s)")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_future_phases_marked_locked(self):
        text = todo_text()
        self.assertIn("Future phases (LOCKED", text, "Part IV must keep future phases marked LOCKED")

    def test_recommended_policy_stated(self):
        text = todo_text().lower()
        self.assertIn("recommended", text)
        self.assertIn("policy", text)
        self.assertIn("latest", text)

    def test_artifact_identity_rule_stated(self):
        text = todo_text()
        self.assertIn("sha256", text)
        self.assertIn("filename", text)


if __name__ == "__main__":
    unittest.main()
