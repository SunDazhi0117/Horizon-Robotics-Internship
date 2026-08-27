#!/usr/bin/env python3
"""Check that the Week 4 portfolio folder is complete and publishable."""

from __future__ import annotations

import re
import sys

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "README_quick_overview.md",
    "RESUME_BULLETS.md",
    "PUBLISHING.md",
    "GIT_COMMIT_CHECK_REPORT.md",
    "docs/01_week_plan.md",
    "docs/02_workflow_understanding.md",
    "docs/03_technical_principles.md",
    "docs/04_validation_and_results.md",
    "docs/05_lessons_and_next_steps.md",
    "docs/06_failure_cases.md",
    "docs/07_agent_prompts.md",
    "docs/08_multi_articulated_scene.md",
    "docs/09_week4_completion_checklist.md",
    "docs/10_scene_versions_comparison.md",
    "docs/11_week5_task_suite_draft.md",
    "docs/12_demo_script.md",
    "docs/13_microwave_drake_validation.md",
    "reports/scene_summary.json",
    "reports/microwave_drake_validation.json",
    "scripts/validate_microwave_drake.py",
    "assets/floor_plan.png",
    "assets/scene_static_overview.png",
    "assets/scene_with_microwave_overview.png",
    "assets/microwave_closed.png",
    "assets/microwave_open.png",
    "assets/multi_articulated_scene_closed.png",
    "assets/multi_articulated_scene_open.png",
    "assets/entry_door_open.png",
    "assets/double_door_cabinet_open.png",
    "assets/week4_articulated_scene_demo.mp4",
]
FORBIDDEN_SUFFIXES = {".blend", ".blend1", ".glb", ".gltf", ".bin"}
SENSITIVE_PATTERNS = {
    "local absolute path": re.compile(r"/home/users/"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    "assigned API key": re.compile(
        r"(?i)\bapi[_-]?key\s*=\s*['\"][^'\"]+['\"]"
    ),
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def emit(status: str, message: str) -> None:
    print(f"{status}: {message}")


def main() -> int:
    failures: list[str] = []

    for relative in REQUIRED:
        path = ROOT / relative
        if path.is_file() and path.stat().st_size > 0:
            emit("PASS", f"{relative} exists")
        else:
            failures.append(f"missing required file: {relative}")
            emit("FAIL", failures[-1])

    forbidden = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden:
        for path in forbidden:
            failures.append(f"large 3D artifact should not be committed: {path}")
            emit("FAIL", failures[-1])
    else:
        emit("PASS", "no GLB, BLEND, or related large 3D files")

    for markdown in ROOT.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                failures.append(
                    f"{label} found in {markdown.relative_to(ROOT)}"
                )
                emit("FAIL", failures[-1])
        for target in MARKDOWN_LINK.findall(text):
            if "://" in target or target.startswith("#"):
                continue
            destination = (
                markdown.parent / target.split("#", maxsplit=1)[0]
            ).resolve()
            if not destination.exists():
                failures.append(
                    f"broken link in {markdown.relative_to(ROOT)}: {target}"
                )
                emit("FAIL", failures[-1])

    if failures:
        emit("RESULT", f"FAIL ({len(failures)} issue(s))")
        return 1
    emit("RESULT", "PASS - portfolio is complete and ready for review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
