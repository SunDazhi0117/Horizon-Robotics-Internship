#!/usr/bin/env python3
"""Combine an existing SceneSmith room and generated furniture into one GLB."""

from __future__ import annotations

import argparse
import json
import math
import sys

from pathlib import Path
from typing import Any

import bpy

from mathutils import Quaternion, Vector


EXTRA_PLACEMENTS = {
    "storage_bookcase_1782812040": {
        "dimensions": (1.2, 0.35, 1.8),
        "translation": (3.35, 1.6, 0.0),
        "rotation_z_degrees": 90.0,
    },
    "storage_console_1782812097": {
        "dimensions": (1.4, 0.4, 0.85),
        "translation": (0.0, 2.4, 0.0),
        "rotation_z_degrees": 180.0,
    },
    "storage_shelving_unit_1782811980": {
        "dimensions": (1.2, 0.35, 1.8),
        "translation": (1.7, -2.35, 0.0),
        "rotation_z_degrees": 0.0,
    },
}


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("scene_dir", type=Path)
    return parser.parse_args(argv)


def mesh_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    if not points:
        raise RuntimeError("No mesh geometry found while calculating bounds")
    return (
        Vector(tuple(min(point[i] for point in points) for i in range(3))),
        Vector(tuple(max(point[i] for point in points) for i in range(3))),
    )


def bounds_dict(bounds: tuple[Vector, Vector]) -> dict[str, list[float]]:
    minimum, maximum = bounds
    return {
        "min": [round(value, 6) for value in minimum],
        "max": [round(value, 6) for value in maximum],
        "dimensions": [round(maximum[i] - minimum[i], 6) for i in range(3)],
    }


def import_furniture(
    glb_path: Path,
    collection: bpy.types.Collection,
    dimensions: tuple[float, float, float],
    translation: tuple[float, float, float],
    rotation: Quaternion,
    room_offset: Vector,
    placement_source: str,
) -> dict[str, Any]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    imported = list(set(bpy.data.objects) - before)
    if not imported:
        raise RuntimeError(f"No objects imported from {glb_path}")

    for obj in imported:
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)

    root = bpy.data.objects.new(f"FURNITURE::{glb_path.stem}", None)
    collection.objects.link(root)
    root["asset_role"] = "furniture"
    root["source_file"] = glb_path.name
    root["placement_source"] = placement_source

    imported_set = set(imported)
    for obj in imported:
        if obj.parent not in imported_set:
            matrix_world = obj.matrix_world.copy()
            obj.parent = root
            obj.matrix_world = matrix_world

    bpy.context.view_layer.update()
    source_min, source_max = mesh_bounds(imported)
    source_size = source_max - source_min
    if min(source_size) <= 0:
        raise RuntimeError(f"Degenerate furniture bounds in {glb_path}")

    root.rotation_mode = "QUATERNION"
    root.rotation_quaternion = rotation
    root.scale = Vector(
        tuple(dimensions[i] / source_size[i] for i in range(3))
    )
    bpy.context.view_layer.update()

    current_min, current_max = mesh_bounds(imported)
    current_center = (current_min + current_max) * 0.5
    target_center = room_offset + Vector(translation)
    root.location += Vector(
        (
            target_center.x - current_center.x,
            target_center.y - current_center.y,
            -current_min.z,
        )
    )
    bpy.context.view_layer.update()

    final_bounds = mesh_bounds(imported)
    return {
        "name": glb_path.stem,
        "node_name": root.name,
        "source_file": glb_path.name,
        "placement_source": placement_source,
        "bounds": bounds_dict(final_bounds),
        "ground_clearance": round(final_bounds[0].z, 6),
    }


def state_placement(
    asset_stem: str, state_objects: dict[str, dict[str, Any]]
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    Quaternion,
] | None:
    for data in state_objects.values():
        if data.get("object_type") != "furniture":
            continue
        sdf_path = Path(data.get("sdf_path", ""))
        if sdf_path.parent.name != asset_stem:
            continue

        bbox_min = data["bbox_min"]
        bbox_max = data["bbox_max"]
        dimensions = tuple(
            float(bbox_max[i] - bbox_min[i]) for i in range(3)
        )
        translation = tuple(float(value) for value in data["transform"]["translation"])
        wxyz = data["transform"]["rotation_wxyz"]
        rotation = Quaternion((wxyz[0], wxyz[1], wxyz[2], wxyz[3]))
        return dimensions, translation, rotation
    return None


def aabb_overlap(
    left: dict[str, Any], right: dict[str, Any], tolerance: float = 0.01
) -> bool:
    left_bounds = left["bounds"]
    right_bounds = right["bounds"]
    return all(
        left_bounds["min"][axis] < right_bounds["max"][axis] - tolerance
        and left_bounds["max"][axis] > right_bounds["min"][axis] + tolerance
        for axis in range(3)
    )


def main() -> None:
    args = parse_args()
    scene_dir = args.scene_dir.resolve()
    room_blend = scene_dir / "floor_plans/final_floor_plan/floor_plan.blend"
    furniture_dir = scene_dir / "room_studio/generated_assets/furniture/geometry"
    state_path = (
        scene_dir
        / "room_studio/scene_states/scene_after_furniture/scene_state.json"
    )
    output_blend = scene_dir / "complete_room_with_furniture.blend"
    output_glb = scene_dir / "complete_room_with_furniture.glb"
    report_path = scene_dir / "complete_room_with_furniture_report.json"

    required = [room_blend, furniture_dir, state_path]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Required input does not exist: {path}")

    furniture_glbs = sorted(furniture_dir.glob("*.glb"))
    if len(furniture_glbs) != 7:
        raise RuntimeError(
            f"Expected exactly 7 furniture GLBs, found {len(furniture_glbs)}"
        )

    state = json.loads(state_path.read_text())
    room_geometry = state["room_geometry"]
    state_objects = state["objects"]

    bpy.ops.wm.open_mainfile(filepath=str(room_blend))
    for obj in list(bpy.data.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            obj["asset_role"] = "room"

    room_objects = list(bpy.context.scene.objects)
    floor_candidates = [
        obj
        for obj in room_objects
        if obj.type == "MESH"
        and obj.dimensions.z <= 0.2
        and obj.dimensions.x * obj.dimensions.y > 10
    ]
    if not floor_candidates:
        raise RuntimeError("Could not identify the room floor in floor_plan.blend")
    floor = max(floor_candidates, key=lambda obj: obj.dimensions.x * obj.dimensions.y)
    floor_min, floor_max = mesh_bounds([floor])
    floor_center = (floor_min + floor_max) * 0.5

    state_floor = room_geometry["floor"]
    state_floor_center = Vector(
        tuple(
            (state_floor["bbox_min"][i] + state_floor["bbox_max"][i]) * 0.5
            for i in range(3)
        )
    )
    room_offset = Vector(
        (
            floor_center.x - state_floor_center.x,
            floor_center.y - state_floor_center.y,
            0.0,
        )
    )

    furniture_collection = bpy.data.collections.new("Furniture")
    bpy.context.scene.collection.children.link(furniture_collection)

    furniture_report = []
    for glb_path in furniture_glbs:
        placement = state_placement(glb_path.stem, state_objects)
        if placement is not None:
            dimensions, translation, rotation = placement
            placement_source = "scene_after_furniture"
        else:
            extra = EXTRA_PLACEMENTS.get(glb_path.stem)
            if extra is None:
                raise RuntimeError(
                    f"No state or deterministic placement for {glb_path.name}"
                )
            dimensions = extra["dimensions"]
            translation = extra["translation"]
            rotation = Quaternion(
                (0.0, 0.0, 1.0),
                math.radians(extra["rotation_z_degrees"]),
            )
            placement_source = "deterministic_extra"

        furniture_report.append(
            import_furniture(
                glb_path=glb_path,
                collection=furniture_collection,
                dimensions=dimensions,
                translation=translation,
                rotation=rotation,
                room_offset=room_offset,
                placement_source=placement_source,
            )
        )

    floor_xy = {
        "min_x": floor_min.x,
        "max_x": floor_max.x,
        "min_y": floor_min.y,
        "max_y": floor_max.y,
    }
    wall_margin = float(room_geometry["wall_thickness"]) * 0.5
    for item in furniture_report:
        bounds = item["bounds"]
        item["grounded"] = abs(item["ground_clearance"]) <= 0.002
        item["inside_room"] = (
            bounds["min"][0] >= floor_xy["min_x"] + wall_margin - 0.01
            and bounds["max"][0] <= floor_xy["max_x"] - wall_margin + 0.01
            and bounds["min"][1] >= floor_xy["min_y"] + wall_margin - 0.01
            and bounds["max"][1] <= floor_xy["max_y"] - wall_margin + 0.01
        )

    overlaps = []
    for index, left in enumerate(furniture_report):
        for right in furniture_report[index + 1 :]:
            if aabb_overlap(left, right):
                overlaps.append([left["name"], right["name"]])

    bpy.context.scene["scene_type"] = "complete_room_with_furniture"
    bpy.context.scene["furniture_count"] = len(furniture_report)
    bpy.context.scene["room_source"] = str(room_blend)
    bpy.context.scene["state_source"] = str(state_path)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
    bpy.ops.export_scene.gltf(
        filepath=str(output_glb),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_extras=True,
        use_visible=True,
    )

    if not output_glb.is_file() or output_glb.stat().st_size == 0:
        raise RuntimeError(f"GLB export failed: {output_glb}")

    report = {
        "scene_dir": str(scene_dir),
        "room_source": str(room_blend),
        "state_source": str(state_path),
        "output_blend": str(output_blend),
        "output_glb": str(output_glb),
        "output_blend_bytes": output_blend.stat().st_size,
        "output_glb_bytes": output_glb.stat().st_size,
        "room_mesh_count": sum(obj.type == "MESH" for obj in room_objects),
        "room_includes": {
            "floor": True,
            "walls": len(room_geometry["walls"]),
            "windows": sum(
                opening["opening_type"] == "window"
                for opening in room_geometry["openings"]
            ),
        },
        "room_offset": [round(value, 6) for value in room_offset],
        "furniture_count": len(furniture_report),
        "state_placed_furniture_count": sum(
            item["placement_source"] == "scene_after_furniture"
            for item in furniture_report
        ),
        "deterministic_extra_furniture_count": sum(
            item["placement_source"] == "deterministic_extra"
            for item in furniture_report
        ),
        "all_furniture_grounded": all(
            item["grounded"] for item in furniture_report
        ),
        "all_furniture_inside_room": all(
            item["inside_room"] for item in furniture_report
        ),
        "furniture_aabb_overlaps": overlaps,
        "furniture": furniture_report,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    print(f"Saved Blender scene: {output_blend}")
    print(f"Saved complete GLB: {output_glb}")
    print(f"Saved validation report: {report_path}")
    print(f"Furniture: {len(furniture_report)}")
    print(f"All grounded: {report['all_furniture_grounded']}")
    print(f"All inside room: {report['all_furniture_inside_room']}")
    print(f"AABB overlaps: {len(overlaps)}")


if __name__ == "__main__":
    main()
