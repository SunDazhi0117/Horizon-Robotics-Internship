#!/usr/bin/env python3
"""Print the validated Week 4 scene summary."""

from __future__ import annotations

import json

from pathlib import Path


REPORT = (
    Path(__file__).resolve().parents[1] / "reports" / "scene_summary.json"
)


def main() -> None:
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    room = data["room"]
    articulated = data["articulated_objects"]
    validation = data["validation"]
    print(f"Scene version: {data['scene_version']}")
    print(
        "Room: "
        f"floor={room['floor']}, walls={room['walls']}, "
        f"windows={room['windows']}"
    )
    print(f"Static furniture: {data['static_furniture_count']}")
    print(f"Articulated objects: {len(articulated)}")
    for item in articulated:
        print(f"  - {item['name']}: {item['joint_count']} joint(s)")
    print(f"Total joints: {sum(item['joint_count'] for item in articulated)}")
    print(f"Sampled poses: {validation['sampled_poses']}")
    print(
        "Validated unintended collisions: "
        f"{validation['normal_path_unintended_collisions']}"
    )
    print(
        "Interaction targets: "
        f"{validation['reachable_targets']}/{validation['target_count']} "
        "reachable"
    )
    print(
        "Connected free-space diagnostic: "
        f"{validation['connected_free_space_ratio']:.6f}"
    )
    print(f"Browser controls: {validation['browser_joint_controls']}")
    print(f"Browser: {validation['browser_status']}")
    print(f"Status: {validation['result']}")
    print(f"Constraint: {data['known_constraint']}")


if __name__ == "__main__":
    main()
