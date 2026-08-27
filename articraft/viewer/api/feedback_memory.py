from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


MAX_MEMORY_ENTRIES = 2000
KEYWORD_RE = re.compile(r"[a-zA-Z0-9_+-]{3,}")


@dataclass(frozen=True, slots=True)
class FeedbackMemoryEntry:
    feedback_id: str
    created_at: str
    record_id: str | None
    object_type: str
    issue_types: list[str]
    problem: str
    fix: str
    tags: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "feedback_id": self.feedback_id,
            "created_at": self.created_at,
            "record_id": self.record_id,
            "object_type": self.object_type,
            "issue_types": self.issue_types,
            "problem": self.problem,
            "fix": self.fix,
            "tags": self.tags,
        }


def feedback_memory_path(repo_root: Path) -> Path:
    return repo_root / "data" / "feedback_memory" / "feedback.jsonl"


def _normalize_text(value: str, *, max_length: int) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized[:max_length].rstrip()


def _normalize_list(values: list[str] | tuple[str, ...] | None, *, max_items: int) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = _normalize_text(str(value), max_length=64).lower()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
        if len(normalized) >= max_items:
            break
    return normalized


def append_feedback_memory(
    *,
    repo_root: Path,
    record_id: str | None,
    object_type: str,
    issue_types: list[str] | tuple[str, ...] | None,
    problem: str,
    fix: str,
    tags: list[str] | tuple[str, ...] | None,
) -> FeedbackMemoryEntry:
    cleaned_problem = _normalize_text(problem, max_length=4000)
    if not cleaned_problem:
        raise ValueError("Feedback problem is required.")

    entry = FeedbackMemoryEntry(
        feedback_id="fb_" + uuid4().hex[:12],
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        record_id=_normalize_text(record_id or "", max_length=160) or None,
        object_type=_normalize_text(object_type, max_length=160),
        issue_types=_normalize_list(issue_types, max_items=8),
        problem=cleaned_problem,
        fix=_normalize_text(fix, max_length=4000),
        tags=_normalize_list(tags, max_items=16),
    )
    path = feedback_memory_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def load_feedback_memory(repo_root: Path, *, limit: int = MAX_MEMORY_ENTRIES) -> list[FeedbackMemoryEntry]:
    path = feedback_memory_path(repo_root)
    if not path.is_file():
        return []

    entries: list[FeedbackMemoryEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        try:
            entries.append(
                FeedbackMemoryEntry(
                    feedback_id=str(payload.get("feedback_id") or ""),
                    created_at=str(payload.get("created_at") or ""),
                    record_id=(
                        str(payload.get("record_id"))
                        if payload.get("record_id") is not None
                        else None
                    ),
                    object_type=str(payload.get("object_type") or ""),
                    issue_types=[
                        str(item)
                        for item in payload.get("issue_types", [])
                        if isinstance(item, str)
                    ],
                    problem=str(payload.get("problem") or ""),
                    fix=str(payload.get("fix") or ""),
                    tags=[str(item) for item in payload.get("tags", []) if isinstance(item, str)],
                )
            )
        except Exception:
            continue
    return entries


def _keywords(text: str) -> set[str]:
    return {match.group(0).lower() for match in KEYWORD_RE.finditer(text)}


def select_relevant_feedback(
    *,
    repo_root: Path,
    prompt: str,
    object_hint: str = "",
    limit: int = 6,
) -> list[FeedbackMemoryEntry]:
    entries = load_feedback_memory(repo_root)
    if not entries:
        return []

    query_tokens = _keywords(f"{prompt} {object_hint}")
    scored: list[tuple[int, int, FeedbackMemoryEntry]] = []
    for recency_index, entry in enumerate(reversed(entries)):
        entry_text = " ".join(
            [
                entry.object_type,
                entry.problem,
                entry.fix,
                " ".join(entry.issue_types),
                " ".join(entry.tags),
            ]
        )
        entry_tokens = _keywords(entry_text)
        overlap = len(query_tokens & entry_tokens) if query_tokens else 0
        issue_bonus = 1 if any(item in {"motion", "collision", "shape", "detail"} for item in entry.issue_types) else 0
        score = overlap * 4 + issue_bonus
        if score > 0 or recency_index < limit:
            scored.append((score, -recency_index, entry))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [entry for _, _, entry in scored[:limit]]


def render_feedback_memory(entries: list[FeedbackMemoryEntry]) -> str:
    if not entries:
        return ""

    blocks = [
        "Relevant Articraft feedback memory. Treat these as lessons from prior generated objects; "
        "use them only when applicable and do not overfit unrelated objects:"
    ]
    for index, entry in enumerate(entries, start=1):
        labels = ", ".join([entry.object_type, *entry.issue_types, *entry.tags]).strip(", ")
        blocks.append(
            f"{index}. Context: {labels or 'general'}\n"
            f"   Problem to avoid: {entry.problem}\n"
            f"   Correction pattern: {entry.fix or 'Preserve visual accuracy and avoid repeating this issue.'}"
        )
    return "\n".join(blocks)
