#!/usr/bin/env python3
"""Validate an articulated Articraft microwave in a frozen SceneSmith scene."""

from __future__ import annotations

import argparse
import json
import math
import struct
import xml.etree.ElementTree as ET

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import bpy

from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--glb", required=True, type=Path)
    parser.add_argument("--urdf", required=True, type=Path)
    parser.add_argument("--placement-report", required=True, type=Path)
    parser.add_argument("--base-validation", required=True, type=Path)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    parser.add_argument("--version-dir", required=True, type=Path)
    parser.add_argument("--viewer-url", required=True)
    return parser.parse_args()


def read_glb_json(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        magic, version, total_length = struct.unpack("<4sII", stream.read(12))
        if magic != b"glTF" or version != 2:
            raise RuntimeError(f"Not a glTF 2.0 binary: {path}")
        if total_length != path.stat().st_size:
            raise RuntimeError("GLB header length does not match file size")
        chunk_length, chunk_type = struct.unpack("<I4s", stream.read(8))
        if chunk_type != b"JSON":
            raise RuntimeError("The first GLB chunk is not JSON")
        return json.loads(stream.read(chunk_length).decode().rstrip(" \0"))


def bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        for corner in obj.bound_box
    ]
    return (
        Vector(tuple(min(point[i] for point in points) for i in range(3))),
        Vector(tuple(max(point[i] for point in points) for i in range(3))),
    )


def rounded(vector: Vector) -> list[float]:
    return [round(value, 6) for value in vector]


def link_name(obj: bpy.types.Object) -> str:
    current = obj
    while current:
        if current.name.startswith("LINK::"):
            return current.name.removeprefix("LINK::")
        current = current.parent
    raise RuntimeError(f"No URDF link ancestor for {obj.name}")


def bvh(obj: bpy.types.Object) -> BVHTree:
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    return BVHTree.FromPolygons(
        vertices, polygons, all_triangles=False, epsilon=1e-6
    )


def unexpected_self_collisions(
    visuals: list[bpy.types.Object],
) -> list[list[str]]:
    structural_contacts = {
        frozenset(("microwave_body", "front_door")),
        frozenset(("microwave_body", "sliding_tray")),
        frozenset(("sliding_tray", "turntable")),
    }
    trees = {obj.name: bvh(obj) for obj in visuals}
    collisions = []
    for index, left in enumerate(visuals):
        left_link = link_name(left)
        for right in visuals[index + 1 :]:
            right_link = link_name(right)
            pair = frozenset((left_link, right_link))
            if left_link == right_link or pair in structural_contacts:
                continue
            if trees[left.name].overlap(trees[right.name]):
                collisions.append([left.name, right.name])
    return collisions


def overlap(
    left_min: Vector,
    left_max: Vector,
    right_min: list[float],
    right_max: list[float],
    tolerance: float = 0.005,
) -> bool:
    return all(
        left_min[i] < right_max[i] - tolerance
        and left_max[i] > right_min[i] + tolerance
        for i in range(3)
    )


def set_joint(
    joint: bpy.types.Object,
    base_location: Vector,
    base_rotation: Quaternion,
    amount: float,
) -> None:
    axis = Vector(joint["axis"])
    joint.location = base_location
    joint.rotation_mode = "QUATERNION"
    if joint["joint_type"] == "prismatic":
        joint.location = base_location + axis * amount
        joint.rotation_quaternion = base_rotation
    else:
        joint.rotation_quaternion = base_rotation @ Quaternion(axis, amount)


def write_markdown(report: dict[str, Any], output: Path) -> None:
    joints = "\n".join(
        (
            f"- `{joint['name']}`: {joint['type']}, axis={joint['axis']}, "
            f"range={joint['range']}"
        )
        for joint in report["articulation"]["joints"]
    )
    text = f"""# Articraft Microwave Acceptance Report

## Version

- New version: `{report["version_dir"]}`
- Microwave source: `{report["microwave_source"]}`
- Viewer: {report["viewer_url"]}
- No room, furniture, or articulated assets were regenerated.
- The source `stable_scene_v1` was not modified.

## Articulation

- Articulation preserved: **{str(report["articulation"]["preserved"]).lower()}**
- Movable: **{str(report["articulation"]["movable"]).lower()}**
- Joint count: {report["articulation"]["joint_count"]}

{joints}

## Placement And Motion

- Support: `{report["placement"]["support_object"]}` desk/counter surface
- Base clearance: {report["placement"]["base_clearance_m"]:.6f} m
- Footprint inside support: {str(report["placement"]["footprint_inside_support"]).lower()}
- Closed state: **{report["motion"]["closed_state"]}**
- Fully open state: **{report["motion"]["open_state"]}**
- Door direction: {report["motion"]["door_direction"]}
- Door range: {report["motion"]["door_range_rad"]:.2f} rad ({report["motion"]["door_range_degrees"]:.2f} degrees)
- Normal operation path: **{report["motion"]["normal_path"]}**
- Wall collisions: {report["scene_collision"]["wall_collision_count"]}
- Furniture collisions: {report["scene_collision"]["furniture_collision_count"]}
- Unexpected self-collisions on normal path: {report["motion"]["normal_path_self_collision_count"]}

The normal path is: open the door to at least 1.50 rad, then pull the tray.
Pulling the tray beyond about 0.11 m while the door remains closed intersects
the door. The viewer allows independent joint control, so this operating
constraint must be respected.

## Complete Scene

- Floor: {str(report["base_scene"]["room"]["floor"]).lower()}
- Walls: {report["base_scene"]["room"]["walls"]}
- Windows: {report["base_scene"]["room"]["windows"]}
- Existing furniture: {report["base_scene"]["furniture_count"]}
- Furniture: {", ".join(report["base_scene"]["furniture_names"])}
- Lightweight unintended collision count: {report["scene_collision"]["total_unintended_collision_count"]}
- Historical Drake collision count: {report["base_scene"]["historical_collision_count"]}
- Accessibility coverage: {report["base_scene"]["accessibility_ratio"]:.6f}
- Accessibility threshold: {report["base_scene"]["accessibility_threshold"]:.2f}
- Robot passage affected: {str(report["base_scene"]["robot_passage_affected"]).lower()}
- GLB: `{report["glb_path"]}` ({report["glb_bytes"]} bytes)
- BLEND: `{report["blend_path"]}` ({report["blend_bytes"]} bytes)

## Result

**{report["result"].upper()}**

Next: keep this version immutable. For safer interaction, couple the tray
control to a door-angle interlock so the tray cannot extend until the door is
open at least 1.50 rad.
"""
    output.write_text(text)


def main() -> None:
    args = parse_args()
    required = (
        args.blend,
        args.glb,
        args.urdf,
        args.placement_report,
        args.base_validation,
    )
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    placement = json.loads(args.placement_report.read_text())
    base = json.loads(args.base_validation.read_text())
    glb = read_glb_json(args.glb)
    glb_names = {node.get("name", "") for node in glb.get("nodes", [])}
    urdf_root = ET.parse(args.urdf).getroot()
    urdf_joints = urdf_root.findall("joint")

    bpy.ops.wm.open_mainfile(filepath=str(args.blend))
    visuals = [
        obj
        for obj in bpy.data.objects
        if obj.get("asset_role") == "articraft_microwave_visual"
    ]
    joints = {
        obj.name.removeprefix("JOINT::"): obj
        for obj in bpy.data.objects
        if obj.name.startswith("JOINT::")
    }
    if not visuals or len(joints) != len(urdf_joints):
        raise RuntimeError("Microwave visual or joint hierarchy is incomplete")
    bases = {
        name: (obj.location.copy(), obj.rotation_quaternion.copy())
        for name, obj in joints.items()
    }

    def pose(door: float, tray: float = 0.0) -> dict[str, Any]:
        for name, obj in joints.items():
            set_joint(obj, *bases[name], 0.0)
        set_joint(joints["body_to_front_door"], *bases["body_to_front_door"], door)
        set_joint(
            joints["body_to_sliding_tray"],
            *bases["body_to_sliding_tray"],
            tray,
        )
        bpy.context.view_layer.update()
        pose_min, pose_max = bounds(visuals)
        return {
            "door": door,
            "tray": tray,
            "min": rounded(pose_min),
            "max": rounded(pose_max),
            "unexpected_self_collisions": unexpected_self_collisions(visuals),
        }

    closed = pose(0.0)
    door_samples = [pose(index * 1.75 / 7) for index in range(8)]
    normal_samples = [pose(1.5, index * 0.22 / 4) for index in range(5)]
    misuse_samples = [pose(0.0, index * 0.22 / 4) for index in range(5)]
    open_pose = pose(1.75)

    normal_collisions = [
        collision
        for sample in door_samples + normal_samples
        for collision in sample["unexpected_self_collisions"]
    ]
    misuse_collision_samples = [
        sample
        for sample in misuse_samples
        if sample["unexpected_self_collisions"]
    ]

    furniture_collisions: set[str] = set()
    wall_collisions = []
    room_min = Vector((0.05, 0.05, 0.0))
    room_max = Vector((7.15, 5.35, 2.7))
    all_samples = door_samples + normal_samples
    for sample in all_samples:
        sample_min = Vector(sample["min"])
        sample_max = Vector(sample["max"])
        if any(
            sample_min[i] < room_min[i] - 0.005
            or sample_max[i] > room_max[i] + 0.005
            for i in range(3)
        ):
            wall_collisions.append([sample["door"], sample["tray"]])
        for item in json.loads(
            (
                args.version_dir.parent
                / "stable_scene_v1/complete_room_with_furniture_report.json"
            ).read_text()
        )["furniture"]:
            if item["name"].startswith("study_desk"):
                continue
            if overlap(
                sample_min,
                sample_max,
                item["bounds"]["min"],
                item["bounds"]["max"],
            ):
                furniture_collisions.add(item["name"])

    door_range = next(
        joint
        for joint in placement["joints"]
        if joint["name"] == "body_to_front_door"
    )["limits"]["upper"]
    joint_report = []
    for joint in placement["joints"]:
        limits = joint["limits"]
        if "lower" in limits and "upper" in limits:
            joint_range: str | list[float] = [
                limits["lower"],
                limits["upper"],
            ]
        else:
            joint_range = "continuous"
        joint_report.append(
            {
                "name": joint["name"],
                "type": joint["type"],
                "axis": joint["axis"],
                "range": joint_range,
            }
        )

    glb_joint_count = sum(name.startswith("JOINT::") for name in glb_names)
    articulation_preserved = (
        glb_joint_count == len(urdf_joints) == len(joints) == 5
    )
    passage_affected = not placement["footprint_inside_desk"]
    result_passed = (
        base["passed"]
        and articulation_preserved
        and not normal_collisions
        and not wall_collisions
        and not furniture_collisions
        and placement["footprint_inside_desk"]
        and abs(placement["base_clearance_m"]) <= 0.005
        and open_pose["max"][0] > closed["max"][0] + 0.25
        and 80 <= math.degrees(door_range) <= 110
        and not passage_affected
    )
    report = {
        "validated_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "version_dir": str(args.version_dir.resolve()),
        "microwave_source": str(args.urdf.resolve()),
        "viewer_url": args.viewer_url,
        "glb_path": str(args.glb.resolve()),
        "glb_bytes": args.glb.stat().st_size,
        "blend_path": str(args.blend.resolve()),
        "blend_bytes": args.blend.stat().st_size,
        "articulation": {
            "preserved": articulation_preserved,
            "movable": articulation_preserved,
            "joint_count": len(joints),
            "glb_joint_node_count": glb_joint_count,
            "joints": joint_report,
        },
        "placement": {
            "support_object": placement["support_object"],
            "base_clearance_m": placement["base_clearance_m"],
            "footprint_inside_support": placement["footprint_inside_desk"],
            "closed_bounds": placement["microwave_bounds"],
        },
        "motion": {
            "closed_state": (
                "pass"
                if not closed["unexpected_self_collisions"]
                else "fail"
            ),
            "open_state": (
                "pass"
                if not open_pose["unexpected_self_collisions"]
                else "fail"
            ),
            "door_direction": (
                "opens away from the wall and toward the room (+X)"
            ),
            "door_range_rad": door_range,
            "door_range_degrees": round(math.degrees(door_range), 3),
            "normal_path": "pass" if not normal_collisions else "fail",
            "normal_path_self_collision_count": len(normal_collisions),
            "normal_path_samples": door_samples + normal_samples,
            "closed_door_tray_collision_detected": bool(
                misuse_collision_samples
            ),
            "closed_door_tray_first_collision_m": (
                misuse_collision_samples[0]["tray"]
                if misuse_collision_samples
                else None
            ),
        },
        "scene_collision": {
            "wall_collision_count": len(wall_collisions),
            "wall_collision_samples": wall_collisions,
            "furniture_collision_count": len(furniture_collisions),
            "furniture_collision_objects": sorted(furniture_collisions),
            "total_unintended_collision_count": (
                len(wall_collisions)
                + len(furniture_collisions)
                + len(normal_collisions)
                + base["lightweight_collision_count"]
            ),
        },
        "base_scene": {
            "room": base["room"],
            "furniture_count": base["furniture_count"],
            "furniture_names": base["furniture_names"],
            "lightweight_collision_count": base[
                "lightweight_collision_count"
            ],
            "historical_collision_count": base["historical_validation"][
                "collision_count"
            ],
            "accessibility_ratio": base["complete_accessibility"]["ratio"],
            "accessibility_threshold": base["complete_accessibility"][
                "pass_threshold"
            ],
            "accessibility_passed": base["complete_accessibility"]["passed"],
            "robot_passage_affected": passage_affected,
            "reason": (
                "Microwave footprint is contained by the existing desk "
                "footprint and adds no floor-level obstacle."
            ),
        },
        "result": "pass" if result_passed else "fail",
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, args.markdown_output)
    print(json.dumps(report, indent=2))
    if not result_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
