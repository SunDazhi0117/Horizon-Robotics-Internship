"""Command-line entry point for a configuration-driven task trajectory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .executor import TaskExecutor, load_task_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a reusable task trajectory from YAML.",
    )
    parser.add_argument("config", type=Path, help="YAML task configuration")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON path for the complete generated trajectory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_task_config(args.config)
    result = TaskExecutor().execute(config)

    if args.output is not None:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    summary = {
        "task_name": result.task_name,
        "state_count": len(result.states),
        "action_count": len(result.action_ranges),
        "actions": [
            action_range.to_dict()
            for action_range in result.action_ranges
        ],
        "final_state": result.final_state.to_dict(),
        "output": None if args.output is None else str(output),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
