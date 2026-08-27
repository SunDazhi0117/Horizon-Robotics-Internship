#!/usr/bin/env python3
"""Run lightweight validation for an exported complete SceneSmith scene."""

from __future__ import annotations

import argparse
import json
import math
import re
import struct

from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene_dir", type=Path)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    parser.add_argument("--version", default="stable_scene_v1")
    return parser.parse_args()


def read_glb_json(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        magic, version, total_length = struct.unpack("<4sII", stream.read(12))
        if magic != b"glTF" or version != 2:
            raise RuntimeError(f"Not a glTF 2.0 binary: {path}")
        if total_length != path.stat().st_size:
            raise RuntimeError(
                f"GLB header length {total_length} != file size {path.stat().st_size}"
            )
        chunk_length, chunk_type = struct.unpack("<I4s", stream.read(8))
        if chunk_type != b"JSON":
            raise RuntimeError("The first GLB chunk is not JSON")
        return json.loads(stream.read(chunk_length).decode("utf-8").rstrip(" \0"))


def aabb_overlap(
    left: dict[str, Any], right: dict[str, Any], tolerance: float = 0.01
) -> bool:
    return all(
        left["bounds"]["min"][axis]
        < right["bounds"]["max"][axis] - tolerance
        and left["bounds"]["max"][axis]
        > right["bounds"]["min"][axis] + tolerance
        for axis in range(3)
    )


def nearest_free(
    desired: tuple[int, int], free: set[tuple[int, int]]
) -> tuple[int, int]:
    if desired in free:
        return desired
    return min(
        free,
        key=lambda cell: (cell[0] - desired[0]) ** 2
        + (cell[1] - desired[1]) ** 2,
    )


def check_accessibility(
    state: dict[str, Any],
    export_report: dict[str, Any],
    resolution: float = 0.05,
    robot_radius: float = 0.22,
) -> dict[str, Any]:
    floor = state["room_geometry"]["floor"]
    offset_x, offset_y, _ = export_report["room_offset"]
    min_x = floor["bbox_min"][0] + offset_x + robot_radius
    max_x = floor["bbox_max"][0] + offset_x - robot_radius
    min_y = floor["bbox_min"][1] + offset_y + robot_radius
    max_y = floor["bbox_max"][1] + offset_y - robot_radius

    columns = math.floor((max_x - min_x) / resolution) + 1
    rows = math.floor((max_y - min_y) / resolution) + 1
    free: set[tuple[int, int]] = set()
    furniture = export_report["furniture"]
    for column in range(columns):
        x = min_x + column * resolution
        for row in range(rows):
            y = min_y + row * resolution
            blocked = any(
                item["bounds"]["min"][0] - robot_radius <= x
                <= item["bounds"]["max"][0] + robot_radius
                and item["bounds"]["min"][1] - robot_radius <= y
                <= item["bounds"]["max"][1] + robot_radius
                for item in furniture
            )
            if not blocked:
                free.add((column, row))

    entrance = next(
        opening
        for opening in state["room_geometry"]["openings"]
        if opening["opening_type"] == "door"
    )
    start_x = entrance["center_world"][0] + offset_x
    start_y = entrance["center_world"][1] + offset_y + robot_radius + 0.05
    desired = (
        round((start_x - min_x) / resolution),
        round((start_y - min_y) / resolution),
    )
    start = nearest_free(desired, free)

    reachable = {start}
    queue = deque([start])
    while queue:
        column, row = queue.popleft()
        for neighbor in (
            (column - 1, row),
            (column + 1, row),
            (column, row - 1),
            (column, row + 1),
        ):
            if neighbor in free and neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    ratio = len(reachable) / len(free) if free else 0.0
    pass_threshold = 0.99
    return {
        "method": "2D occupancy grid with inflated furniture AABBs",
        "resolution_m": resolution,
        "robot_radius_m": robot_radius,
        "free_cells": len(free),
        "reachable_cells": len(reachable),
        "ratio": round(ratio, 6),
        "pass_threshold": pass_threshold,
        "passed": ratio >= pass_threshold,
        "fully_connected": ratio >= 0.999,
    }


def find_historical_validation(log_path: Path) -> dict[str, Any]:
    text = log_path.read_text(errors="replace")
    collisions = re.findall(r"Found (\d+) collisions", text)
    reachability = re.findall(
        r"Reachability: regions=(\d+), ratio=([0-9.]+), blockers=([^\n]+)",
        text,
    )
    if not collisions or not reachability:
        raise RuntimeError(f"Historical validation evidence missing from {log_path}")
    regions, ratio, blockers = reachability[-1]
    return {
        "scope": "four furniture items in scene_after_furniture",
        "source_log": str(log_path),
        "collision_count": int(collisions[-1]),
        "reachability_regions": int(regions),
        "reachability_ratio": float(ratio),
        "blockers": blockers.strip(),
    }


def proportion_warnings(furniture: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for item in furniture:
        name = item["name"]
        width, depth, height = item["bounds"]["dimensions"]
        horizontal_depth = min(width, depth)
        if "shelving_unit_1782811629" in name and horizontal_depth < 0.25:
            warnings.append(
                f"{name}: depth {horizontal_depth:.3f} m is visibly too thin"
            )
        if name.startswith("study_desk") and height > 0.85:
            warnings.append(f"{name}: height {height:.3f} m is higher than typical")
        if name.startswith("kitchen_base_counter") and height > 1.1:
            warnings.append(f"{name}: height {height:.3f} m is higher than typical")
    return warnings


def write_markdown(report: dict[str, Any], path: Path) -> None:
    objects = "\n".join(f"- {name}" for name in report["furniture_names"])
    warnings = report["proportion_warnings"]
    warning_text = "\n".join(f"- {warning}" for warning in warnings)
    if not warning_text:
        warning_text = "- None"
    text = f"""# stable_scene_v1 Acceptance Report

- Frozen at: {report["frozen_at"]}
- Source scene: `{report["source_scene"]}`
- GLB: `complete_room_with_furniture.glb` ({report["glb_bytes"]} bytes)
- Blender: `complete_room_with_furniture.blend` ({report["blend_bytes"]} bytes)
- Viewer: {report["viewer_url"]}

## Contents

- Floor: yes
- Walls: {report["room"]["walls"]}
- Windows: {report["room"]["windows"]}
- Furniture count: {report["furniture_count"]}

{objects}

## Validation

- GLB 2.0 structure: pass
- Furniture nodes in exported GLB: {report["glb_furniture_node_count"]}
- Grounded: {str(report["all_grounded"]).lower()}
- Inside room walls: {str(report["all_inside_room"]).lower()}
- Lightweight AABB collision count: {report["lightweight_collision_count"]}
- Complete-scene accessibility coverage: {report["complete_accessibility"]["ratio"]:.5f}
- Accessibility threshold: {report["complete_accessibility"]["pass_threshold"]:.2f}
- Historical Drake collision count: {report["historical_validation"]["collision_count"]}
- Historical SceneSmith reachability: {report["historical_validation"]["reachability_ratio"]:.2f}

## Known Proportion Warnings

{warning_text}

No room or furniture assets were regenerated while freezing this version.
"""
    path.write_text(text)


def main() -> None:
    args = parse_args()
    scene_dir = args.scene_dir.resolve()
    glb_path = scene_dir / "complete_room_with_furniture.glb"
    blend_path = scene_dir / "complete_room_with_furniture.blend"
    export_report_path = scene_dir / "complete_room_with_furniture_report.json"
    state_path = (
        scene_dir
        / "room_studio/scene_states/scene_after_furniture/scene_state.json"
    )
    room_log = scene_dir / "room_studio/room.log"
    for path in (glb_path, blend_path, export_report_path, state_path, room_log):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Required stable-scene input missing: {path}")

    glb = read_glb_json(glb_path)
    export_report = json.loads(export_report_path.read_text())
    state = json.loads(state_path.read_text())
    node_names = [node.get("name", "") for node in glb.get("nodes", [])]
    furniture_nodes = [
        name for name in node_names if name.startswith("FURNITURE::")
    ]

    collisions = []
    furniture = export_report["furniture"]
    for index, left in enumerate(furniture):
        for right in furniture[index + 1 :]:
            if aabb_overlap(left, right):
                collisions.append([left["name"], right["name"]])

    accessibility = check_accessibility(state, export_report)
    historical = find_historical_validation(room_log)
    warnings = proportion_warnings(furniture)
    room = export_report["room_includes"]
    report = {
        "version": args.version,
        "frozen_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "source_scene": str(scene_dir),
        "viewer_url": (
            "http://127.0.0.1:8899/stable_scene_v1/"
            "complete_scene_viewer.html?model=complete_room_with_furniture.glb"
        ),
        "glb_path": str(glb_path),
        "glb_bytes": glb_path.stat().st_size,
        "blend_path": str(blend_path),
        "blend_bytes": blend_path.stat().st_size,
        "glb_version": 2,
        "glb_node_count": len(glb.get("nodes", [])),
        "glb_mesh_count": len(glb.get("meshes", [])),
        "glb_furniture_node_count": len(furniture_nodes),
        "room": room,
        "furniture_count": len(furniture),
        "furniture_names": [item["name"] for item in furniture],
        "all_grounded": all(item["grounded"] for item in furniture),
        "all_inside_room": all(item["inside_room"] for item in furniture),
        "lightweight_collision_count": len(collisions),
        "lightweight_collision_pairs": collisions,
        "complete_accessibility": accessibility,
        "historical_validation": historical,
        "proportion_warnings": warnings,
    }

    failures = []
    if len(furniture_nodes) != 7:
        failures.append(f"expected 7 GLB furniture nodes, found {len(furniture_nodes)}")
    if not report["all_grounded"]:
        failures.append("one or more furniture objects are floating")
    if not report["all_inside_room"]:
        failures.append("one or more furniture objects cross the room walls")
    if collisions:
        failures.append(f"found {len(collisions)} furniture AABB collisions")
    if not accessibility["passed"]:
        failures.append(
            f"complete-scene accessibility is only {accessibility['ratio']:.3f}"
        )
    if historical["collision_count"] != 0:
        failures.append("historical Drake collision count is nonzero")
    if historical["reachability_ratio"] != 1.0:
        failures.append("historical SceneSmith reachability is not 1.0")
    report["passed"] = not failures
    report["failures"] = failures

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, args.markdown_output)

    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
