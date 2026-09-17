#!/usr/bin/env python3
"""generate_compatibility_report.py — WSA Compatibility Operations & Scoring Engine (Epic PR4, Task PR4.3).

Ingests verified application records, validates them against compatibility/schema.json,
computes category and channel compatibility scores, and emits actionable recommendations
for Standard Edition (Magisk) and Banking Edition (Vanilla).

Pure Python standard library.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPAT_DATA_DIR = REPO_ROOT / "compatibility" / "data"
DIST_REPORTS = REPO_ROOT / "dist" / "reports"
DOCS_DIR = REPO_ROOT / "docs"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_compatibility as vc  # noqa: E402


@dataclass
class AppCompatibilitySummary:
    package_id: str
    app_name: str
    category: str
    compatibility_status: str
    play_integrity_required: bool
    tested_wsa_version: str
    tested_root_flavor: str
    verification_status: str
    workaround_steps: Optional[str] = None
    known_issues: Optional[str] = None


@dataclass
class CategoryScore:
    category: str
    total_apps: int
    working_count: int
    workaround_count: int
    broken_count: int
    score_percentage: float


@dataclass
class CompatibilityReport:
    timestamp: str
    total_apps_tested: int
    overall_compatibility_score: float
    category_scores: List[CategoryScore]
    play_integrity_rate: float
    edition_recommendations: Dict[str, str]
    apps: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_apps_tested": self.total_apps_tested,
            "overall_compatibility_score": self.overall_compatibility_score,
            "category_scores": [asdict(cs) for cs in self.category_scores],
            "play_integrity_rate": self.play_integrity_rate,
            "edition_recommendations": self.edition_recommendations,
            "apps": self.apps,
        }


def generate_compatibility_report(data_dir: Path = COMPAT_DATA_DIR) -> CompatibilityReport:
    """Generates an evidence-backed compatibility scoring report."""
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    records: List[Dict[str, Any]] = []
    for f in sorted(data_dir.glob("*.json")):
        if f.is_file() and f.name != "schema.json":
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                errors = vc.validate_record_data(data, str(f))
                if not errors:
                    records.append(data)
            except Exception:
                pass

    if not records:
        raise ValueError(f"No valid compatibility records found in {data_dir}")

    total = len(records)
    working = sum(1 for r in records if r.get("compatibility_status") == "Working")
    workaround = sum(1 for r in records if r.get("compatibility_status") == "Workaround Required")
    broken = sum(1 for r in records if r.get("compatibility_status") == "Broken")
    play_req = sum(1 for r in records if r.get("play_integrity_required") is True)

    # Score: working=100%, workaround=75%, broken=0%
    overall_score = round(((working * 1.0 + workaround * 0.75) / total) * 100.0, 1)
    play_rate = round((play_req / total) * 100.0, 1)

    # Category Breakdown
    categories = sorted(list({r.get("category", "Other") for r in records}))
    cat_scores: List[CategoryScore] = []
    for cat in categories:
        cat_recs = [r for r in records if r.get("category") == cat]
        c_tot = len(cat_recs)
        c_work = sum(1 for r in cat_recs if r.get("compatibility_status") == "Working")
        c_wrk_around = sum(1 for r in cat_recs if r.get("compatibility_status") == "Workaround Required")
        c_brk = sum(1 for r in cat_recs if r.get("compatibility_status") == "Broken")
        c_score = round(((c_work * 1.0 + c_wrk_around * 0.75) / c_tot) * 100.0, 1)
        cat_scores.append(
            CategoryScore(
                category=cat,
                total_apps=c_tot,
                working_count=c_work,
                workaround_count=c_wrk_around,
                broken_count=c_brk,
                score_percentage=c_score,
            )
        )

    edition_recommendations = {
        "standard_edition": "Recommended for general consumers, modders, and power users needing root privilege management. Verified with Magisk Stable (v30.6+) and Play Store Pico.",
        "banking_edition": "Recommended for financial, banking, and enterprise apps (Paytm, PhonePe, YONO) requiring unrooted clean ramdisks and zero su binary detection.",
        "arm64_guidance": "Recommended for Snapdragon X Elite / Copilot+ PCs via native arm64 build scripts. Reference /arm64 for self-build instructions.",
    }

    return CompatibilityReport(
        timestamp=now_iso,
        total_apps_tested=total,
        overall_compatibility_score=overall_score,
        category_scores=cat_scores,
        play_integrity_rate=play_rate,
        edition_recommendations=edition_recommendations,
        apps=records,
    )


def format_markdown_report(report: CompatibilityReport) -> str:
    """Formats report into Markdown document."""
    lines = [
        "# Emberbird Application Compatibility Operations Report",
        "",
        f"**Generated**: `{report.timestamp}`  ",
        f"**Total Applications Tested**: `{report.total_apps_tested}`  ",
        f"**Overall Compatibility Score**: `{report.overall_compatibility_score}%`  ",
        f"**Play Integrity Requirement Rate**: `{report.play_integrity_rate}%`  ",
        "",
        "## Category Performance Matrix",
        "",
        "| Category | Apps Tested | Working | Workaround | Broken | Compatibility Score |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for cs in report.category_scores:
        lines.append(
            f"| **{cs.category}** | {cs.total_apps} | {cs.working_count} | {cs.workaround_count} | {cs.broken_count} | **{cs.score_percentage}%** |"
        )

    lines.extend([
        "",
        "## Edition Recommendations",
        f"- **Standard Edition**: {report.edition_recommendations['standard_edition']}",
        f"- **Banking Edition**: {report.edition_recommendations['banking_edition']}",
        f"- **Snapdragon X Elite (ARM64)**: {report.edition_recommendations['arm64_guidance']}",
        "",
        "## Tested Applications Catalog",
        "",
        "| App Name | Package ID | Category | Status | Play Integrity | Tested WSA | Root Flavor |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for app in report.apps:
        pi_badge = "Required" if app.get("play_integrity_required") else "Optional"
        lines.append(
            f"| **{app['app_name']}** | `{app['package_id']}` | {app['category']} | **{app['compatibility_status']}** | {pi_badge} | `{app.get('tested_wsa_version', 'N/A')}` | `{app.get('tested_root_flavor', 'N/A')}` |"
        )

    lines.extend([
        "",
        "---",
        "*Report generated by `scripts/generate_compatibility_report.py` under the Emberbird Production Stewardship Edition.*",
        "",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Emberbird Compatibility Scoring Engine (Epic PR4, Task PR4.3)")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    parser.add_argument("--output-dir", type=Path, default=DIST_REPORTS, help="Output directory")

    args = parser.parse_args(argv)

    report = generate_compatibility_report()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "compatibility-report.json"
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    md_path = DOCS_DIR / "COMPATIBILITY_REPORT.md"
    md_path.write_text(format_markdown_report(report), encoding="utf-8")

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("================================================================================")
        print("  Emberbird Application Compatibility Operations (Epic PR4, Task PR4.3)")
        print(f"  Total Tested Apps: {report.total_apps_tested} | Overall Compatibility Score: {report.overall_compatibility_score}%")
        print(f"  Play Integrity Dependency Rate: {report.play_integrity_rate}%")
        print("================================================================================")
        for cs in report.category_scores:
            print(f"  {cs.category:<25} {cs.score_percentage:>5.1f}% ({cs.working_count} working, {cs.workaround_count} workaround, {cs.broken_count} broken)")
        print("================================================================================")
        print(f"[+] Saved JSON report to: {json_path}")
        print(f"[+] Saved Markdown report to: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
