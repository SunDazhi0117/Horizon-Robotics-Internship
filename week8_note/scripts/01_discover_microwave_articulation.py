"""Inspect the existing microwave articulation without changing assets."""

from __future__ import annotations

import json
from pathlib import Path

from week7_note.task_system.level5_integration import create_level5_runtime

from .articulation_discovery import discover_articulation


ROOT = Path(__file__).resolve().parents[1]
TARGET_GEOM = "033_microwave_front_door_handle_bar"
OUTPUT_PATH = ROOT / "results" / "microwave_articulation_discovery.json"


def main() -> None:
    model, data, _, _ = create_level5_runtime()
    info = discover_articulation(model, data, TARGET_GEOM)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(info.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(info.to_dict(), indent=2))


if __name__ == "__main__":
    main()
