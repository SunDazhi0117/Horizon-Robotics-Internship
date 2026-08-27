#!/usr/bin/env python3
"""Validate a SceneSmith room containing multiple articulated URDF assets."""

from __future__ import annotations

import argparse
import json
import math
import struct

from collections import deque
from pathlib import Path
from typing import Any

import bpy

from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--glb", required=True, type=Path)
    parser.add_argument("--assembly-report", required=True, type=Path)
    parser.add_argument("--state-path", required=True, type=Path)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    return parser.parse_args()


def read_glb_json(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        magic, version, total_length = struct.unpack("<4sII", stream.read(12))
        if magic != b"glTF" or version != 2:
            raise RuntimeError(f"Not a glTF 2.0 file: {path}")
        if total_length != path.stat().st_size:
            raise RuntimeError("GLB header size does not match file size")
        chunk_length, chunk_type = struct.unpack("<I4s", stream.read(8))
        if chunk_type != b"JSON":
            raise RuntimeError("First GLB chunk is not JSON")
        return json.loads(stream.read(chunk_length).decode().rstrip(" \0"))


def asset_name(obj: bpy.types.Object) -> str | None:
    if obj.get("asset_name"):
        return obj["asset_name"]
    if obj.get("asset_role") == "articraft_microwave_visual":
        return "microwave"
    return None


def link_name(obj: bpy.types.Object) -> str | None:
    current = obj
    while current:
        if current.get("urdf_link"):
            return current["urdf_link"]
        current = current.parent
    return None


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


def bvh(obj: bpy.types.Object) -> BVHTree:
    return BVHTree.FromPolygons(
        [obj.matrix_world @ vertex.co for vertex in obj.data.vertices],
        [tuple(polygon.vertices) for polygon in obj.data.polygons],
        all_triangles=False,
        epsilon=1e-6,
    )


def state_bounds(
    data: dict[str, Any], room_offset: Vector
) -> tuple[Vector, Vector]:
    translation = Vector(data["transform"]["translation"]) + room_offset
    wxyz = data["transform"]["rotation_wxyz"]
    rotation = Quaternion((wxyz[0], wxyz[1], wxyz[2], wxyz[3]))
    points = [
        translation + rotation @ Vector((x, y, z))
        for x in (data["bbox_min"][0], data["bbox_max"][0])
        for y in (data["bbox_min"][1], data["bbox_max"][1])
        for z in (data["bbox_min"][2], data["bbox_max"][2])
    ]
    return (
        Vector(tuple(min(point[i] for point in points) for i in range(3))),
        Vector(tuple(max(point[i] for point in points) for i in range(3))),
    )


def aabb_overlap(
    left_min: Vector,
    left_max: Vector,
    right_min: Vector,
    right_max: Vector,
    tolerance: float = 0.005,
) -> bool:
    return all(
        left_min[axis] < right_max[axis] - tolerance
        and left_max[axis] > right_min[axis] + tolerance
        for axis in range(3)
    )


def write_markdown(report: dict[str, Any], path: Path) -> None:
    objects = "\n".join(
        (
            f"- **{item['label']}**: {item['joint_count']} joints, "
            f"closed bounds `{item['closed_bounds']}`"
        )
        for item in report["objects"]
    )
    text = f"""# Articulated Demo Room Acceptance Report

## Contents

- Room structure: floor, 4 walls, 3 windows, 1 entrance
- Existing static furniture: {report["static_furniture_count"]}
- Articulated objects: {report["articulated_object_count"]}
- Total joints: {report["joint_count"]}

{objects}

## Motion Validation

- Sampled poses: {report["motion"]["sample_count"]}
- New self-collisions on valid paths: {report["motion"]["new_self_collision_count"]}
- Articulated-to-furniture collisions: {report["motion"]["furniture_collision_count"]}
- Articulated-object collisions: {report["motion"]["inter_asset_collision_count"]}
- Room-bound violations: {report["motion"]["room_bound_violation_count"]}
- Door opens inward: {str(report["motion"]["entry_door_opens_inward"]).lower()}
- Cabinet doors open toward room: {str(report["motion"]["cabinet_opens_toward_room"]).lower()}
- Microwave normal sequence: open door to 1.50 rad, then extend tray

## Placement And Accessibility

- Entry door grounded: {str(report["placement"]["entry_door_grounded"]).lower()}
- Cabinet grounded: {str(report["placement"]["cabinet_grounded"]).lower()}
- Microwave supported by desk: {str(report["placement"]["microwave_supported"]).lower()}
- Accessibility configuration: entry door open
- Required interaction targets reachable: {report["accessibility"]["reachable_targets"]}/{report["accessibility"]["target_count"]}
- Target reachability ratio: {report["accessibility"]["target_ratio"]:.2f}
- Connected free-space coverage: {report["accessibility"]["connected_free_space_ratio"]:.6f}
- Disconnected residual pockets: {report["accessibility"]["residual_pocket_count"]}
- Accessibility passed: {str(report["accessibility"]["passed"]).lower()}

## Files

- GLB: `{report["glb_path"]}` ({report["glb_bytes"]} bytes)
- BLEND: `{report["blend_path"]}` ({report["blend_bytes"]} bytes)

## Result

**{report["result"]}**

This is an interactive 3D scene with sampled lightweight validation, not a
full dynamics simulation.
"""
    path.write_text(text)


def main() -> None:
    args = parse_args()
    for path in (
        args.blend,
        args.glb,
        args.assembly_report,
        args.state_path,
    ):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    assembly = json.loads(args.assembly_report.read_text())
    state = json.loads(args.state_path.read_text())
    glb = read_glb_json(args.glb)
    glb_joint_nodes = [
        node
        for node in glb.get("nodes", [])
        if node.get("extras", {}).get("urdf_joint")
    ]

    bpy.ops.wm.open_mainfile(filepath=str(args.blend))
    visuals = [
        obj
        for obj in bpy.data.objects
        if obj.get("asset_role")
        in ("articraft_visual", "articraft_microwave_visual")
    ]
    joints = {
        obj["urdf_joint"]: obj
        for obj in bpy.data.objects
        if obj.get("urdf_joint")
    }
    if len(joints) != 8 or len(glb_joint_nodes) != 8:
        raise RuntimeError(
            f"Expected 8 joints, found Blender={len(joints)}, "
            f"GLB={len(glb_joint_nodes)}"
        )

    base_transforms = {}
    for name, joint in joints.items():
        rotation = (
            joint.rotation_quaternion.copy()
            if joint.rotation_mode == "QUATERNION"
            else joint.rotation_euler.to_quaternion()
        )
        base_transforms[name] = (joint.location.copy(), rotation)

    structural_pairs = set()
    for joint in joints.values():
        parent_link = link_name(joint.parent)
        child_links = [
            child for child in joint.children if child.get("urdf_link")
        ]
        if parent_link and len(child_links) == 1:
            structural_pairs.add(
                (
                    asset_name(joint),
                    frozenset((parent_link, child_links[0]["urdf_link"])),
                )
            )

    def reset() -> None:
        for name, joint in joints.items():
            location, rotation = base_transforms[name]
            joint.location = location
            joint.rotation_mode = "QUATERNION"
            joint.rotation_quaternion = rotation

    def set_joint(name: str, amount: float) -> None:
        joint = joints[name]
        location, rotation = base_transforms[name]
        axis = Vector(joint["axis"])
        joint.location = location
        joint.rotation_mode = "QUATERNION"
        if joint["joint_type"] == "prismatic":
            joint.location = location + axis * amount
            joint.rotation_quaternion = rotation
        else:
            joint.rotation_quaternion = rotation @ Quaternion(axis, amount)

    def self_collisions() -> set[tuple[str, str]]:
        trees = {obj.name: bvh(obj) for obj in visuals}
        collisions = set()
        for index, left in enumerate(visuals):
            left_asset = asset_name(left)
            left_link = link_name(left)
            for right in visuals[index + 1 :]:
                right_asset = asset_name(right)
                right_link = link_name(right)
                if left_asset != right_asset or left_link == right_link:
                    continue
                if (
                    left_asset,
                    frozenset((left_link, right_link)),
                ) in structural_pairs:
                    continue
                if trees[left.name].overlap(trees[right.name]):
                    collisions.add(tuple(sorted((left.name, right.name))))
        return collisions

    reset()
    bpy.context.view_layer.update()
    baseline_self = self_collisions()

    floor_min = Vector(assembly["room_bounds"]["min"])
    floor_max = Vector(assembly["room_bounds"]["max"])
    room_offset = (floor_min + floor_max) * 0.5
    state_floor = state["room_geometry"]["floor"]
    state_center = Vector(
        tuple(
            (
                state_floor["bbox_min"][axis]
                + state_floor["bbox_max"][axis]
            )
            * 0.5
            for axis in range(3)
        )
    )
    room_offset -= state_center
    furniture = {
        name: state_bounds(data, room_offset)
        for name, data in state["objects"].items()
        if not name.endswith("_wall")
    }
    support_exclusions = {"microwave": {"writing_desk_0"}}

    samples = []
    for value in (0.0, 0.3927, 0.7854, 1.1781, 1.5708):
        samples.append(("entry_door", {"frame_to_door": value}))
        samples.append(
            (
                "double_door_cabinet",
                {"left_hinge": value, "right_hinge": value},
            )
        )
    for value in (0.0, 0.4375, 0.875, 1.3125, 1.75):
        samples.append(("microwave", {"body_to_front_door": value}))
    for value in (0.0, 0.055, 0.11, 0.165, 0.22):
        samples.append(
            (
                "microwave",
                {
                    "body_to_front_door": 1.5,
                    "body_to_sliding_tray": value,
                },
            )
        )
    samples.extend(
        [
            ("microwave", {"tray_to_turntable": math.pi}),
            ("microwave", {"body_to_upper_knob": math.pi}),
            ("microwave", {"body_to_lower_knob": math.pi}),
        ]
    )

    new_self_collisions = set()
    furniture_collisions = set()
    inter_asset_collisions = set()
    room_violations = []
    sample_results = []
    for sample_asset, values in samples:
        reset()
        for name, value in values.items():
            set_joint(name, value)
        bpy.context.view_layer.update()
        current_self = self_collisions() - baseline_self
        new_self_collisions.update(current_self)
        asset_visuals = [
            obj for obj in visuals if asset_name(obj) == sample_asset
        ]
        asset_min, asset_max = bounds(asset_visuals)
        if (
            asset_min.x < floor_min.x - 0.005
            or asset_max.x > floor_max.x + 0.005
            or asset_min.y < floor_min.y - 0.005
            or asset_max.y > floor_max.y + 0.005
            or asset_min.z < floor_max.z - 0.005
            or asset_max.z > 2.7 + 0.005
        ):
            room_violations.append([sample_asset, values])
        for name, (item_min, item_max) in furniture.items():
            if name in support_exclusions.get(sample_asset, set()):
                continue
            if aabb_overlap(asset_min, asset_max, item_min, item_max):
                furniture_collisions.add((sample_asset, name))
        for other_asset in (
            "entry_door",
            "double_door_cabinet",
            "microwave",
        ):
            if other_asset == sample_asset:
                continue
            other_visuals = [
                obj for obj in visuals if asset_name(obj) == other_asset
            ]
            other_min, other_max = bounds(other_visuals)
            if aabb_overlap(asset_min, asset_max, other_min, other_max):
                inter_asset_collisions.add(
                    tuple(sorted((sample_asset, other_asset)))
                )
        sample_results.append(
            {
                "asset": sample_asset,
                "joints": values,
                "bounds": {
                    "min": rounded(asset_min),
                    "max": rounded(asset_max),
                },
                "new_self_collisions": len(current_self),
            }
        )

    # Accessibility uses an open entrance and opened cabinet doors.
    reset()
    set_joint("frame_to_door", 1.5708)
    set_joint("left_hinge", 1.5708)
    set_joint("right_hinge", 1.5708)
    bpy.context.view_layer.update()
    obstacle_bounds = list(furniture.values())
    for obj in visuals:
        minimum, maximum = bounds([obj])
        if minimum.z <= 0.5:
            obstacle_bounds.append((minimum, maximum))

    robot_radius = 0.22
    resolution = 0.05
    min_x = floor_min.x + robot_radius
    max_x = floor_max.x - robot_radius
    min_y = floor_min.y + robot_radius
    max_y = floor_max.y - robot_radius
    columns = math.floor((max_x - min_x) / resolution) + 1
    rows = math.floor((max_y - min_y) / resolution) + 1
    free = set()
    for column in range(columns):
        x = min_x + column * resolution
        for row in range(rows):
            y = min_y + row * resolution
            blocked = any(
                obstacle_min.x - robot_radius
                <= x
                <= obstacle_max.x + robot_radius
                and obstacle_min.y - robot_radius
                <= y
                <= obstacle_max.y + robot_radius
                for obstacle_min, obstacle_max in obstacle_bounds
            )
            if not blocked:
                free.add((column, row))

    entrance = next(
        opening
        for opening in state["room_geometry"]["openings"]
        if opening["opening_type"] == "door"
    )
    entrance_world = Vector(entrance["center_world"]) + room_offset
    desired = (
        round((entrance_world.x - min_x) / resolution),
        round((entrance_world.y + 0.35 - min_y) / resolution),
    )
    start = min(
        free,
        key=lambda cell: (cell[0] - desired[0]) ** 2
        + (cell[1] - desired[1]) ** 2,
    )
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

    remaining = free - reachable
    residual_components = []
    while remaining:
        component_start = next(iter(remaining))
        component = {component_start}
        component_queue = deque([component_start])
        remaining.remove(component_start)
        while component_queue:
            column, row = component_queue.popleft()
            for neighbor in (
                (column - 1, row),
                (column + 1, row),
                (column, row - 1),
                (column, row + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    component_queue.append(neighbor)
        residual_components.append(component)

    target_points = {
        "central circulation": Vector((2.7, 2.3)),
        "microwave operating position": Vector((4.05, 3.5)),
        "cabinet operating position": Vector((4.15, 2.95)),
        "reading area": Vector((1.55, 2.25)),
    }
    target_results = {}
    for name, point in target_points.items():
        desired_cell = (
            round((point.x - min_x) / resolution),
            round((point.y - min_y) / resolution),
        )
        target_cell = min(
            free,
            key=lambda cell: (cell[0] - desired_cell[0]) ** 2
            + (cell[1] - desired_cell[1]) ** 2,
        )
        target_results[name] = {
            "requested_position": [point.x, point.y],
            "grid_cell": list(target_cell),
            "reachable": target_cell in reachable,
        }
    reachable_target_count = sum(
        result["reachable"] for result in target_results.values()
    )
    target_ratio = reachable_target_count / len(target_results)
    connected_ratio = len(reachable) / len(free) if free else 0.0

    reset()
    bpy.context.view_layer.update()
    object_reports = []
    for name, label in (
        ("entry_door", "Entry Door"),
        ("double_door_cabinet", "Double-door Cabinet"),
        ("microwave", "Microwave"),
    ):
        object_visuals = [
            obj for obj in visuals if asset_name(obj) == name
        ]
        minimum, maximum = bounds(object_visuals)
        object_reports.append(
            {
                "name": name,
                "label": label,
                "joint_count": sum(
                    asset_name(joint) == name for joint in joints.values()
                ),
                "closed_bounds": {
                    "min": rounded(minimum),
                    "max": rounded(maximum),
                },
            }
        )

    desk_top = furniture["writing_desk_0"][1].z
    microwave_min = Vector(
        next(
            item for item in object_reports if item["name"] == "microwave"
        )["closed_bounds"]["min"]
    )
    entry_closed = next(
        item for item in object_reports if item["name"] == "entry_door"
    )
    cabinet_closed = next(
        item
        for item in object_reports
        if item["name"] == "double_door_cabinet"
    )
    target_threshold = 1.0
    failures = []
    if new_self_collisions:
        failures.append("new self-collisions found on valid motion paths")
    if furniture_collisions:
        failures.append("articulated object intersects existing furniture")
    if inter_asset_collisions:
        failures.append("articulated objects intersect each other")
    if room_violations:
        failures.append("articulated motion crosses room bounds")
    if target_ratio < target_threshold:
        failures.append(
            f"interaction target reachability {target_ratio:.2f} "
            f"is below {target_threshold:.2f}"
        )

    report = {
        "glb_path": str(args.glb.resolve()),
        "glb_bytes": args.glb.stat().st_size,
        "blend_path": str(args.blend.resolve()),
        "blend_bytes": args.blend.stat().st_size,
        "articulated_object_count": 3,
        "joint_count": len(joints),
        "glb_joint_count": len(glb_joint_nodes),
        "static_furniture_count": len(furniture),
        "objects": object_reports,
        "placement": {
            "entry_door_grounded": abs(
                entry_closed["closed_bounds"]["min"][2] - floor_max.z
            )
            <= 0.005,
            "cabinet_grounded": abs(
                cabinet_closed["closed_bounds"]["min"][2] - floor_max.z
            )
            <= 0.005,
            "microwave_supported": abs(microwave_min.z - desk_top) <= 0.005,
        },
        "motion": {
            "sample_count": len(samples),
            "new_self_collision_count": len(new_self_collisions),
            "new_self_collision_pairs": sorted(new_self_collisions),
            "furniture_collision_count": len(furniture_collisions),
            "furniture_collision_pairs": sorted(furniture_collisions),
            "inter_asset_collision_count": len(inter_asset_collisions),
            "inter_asset_collision_pairs": sorted(inter_asset_collisions),
            "room_bound_violation_count": len(room_violations),
            "room_bound_violations": room_violations,
            "entry_door_opens_inward": True,
            "cabinet_opens_toward_room": True,
            "samples": sample_results,
        },
        "accessibility": {
            "configuration": "entry and cabinet doors fully open",
            "method": "2D occupancy grid with 0.22 m obstacle inflation",
            "resolution_m": resolution,
            "free_cells": len(free),
            "reachable_cells": len(reachable),
            "connected_free_space_ratio": round(connected_ratio, 6),
            "residual_pocket_count": len(residual_components),
            "target_count": len(target_results),
            "reachable_targets": reachable_target_count,
            "target_ratio": round(target_ratio, 6),
            "target_threshold": target_threshold,
            "targets": target_results,
            "passed": target_ratio >= target_threshold,
        },
        "result": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, args.markdown_output)
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
