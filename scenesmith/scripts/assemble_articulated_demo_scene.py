#!/usr/bin/env python3
"""Assemble a SceneSmith room with multiple existing Articraft URDF assets."""

from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any

import bpy

from mathutils import Euler, Quaternion, Vector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-blend", required=True, type=Path)
    parser.add_argument("--state-path", required=True, type=Path)
    parser.add_argument("--door-urdf", required=True, type=Path)
    parser.add_argument("--cabinet-urdf", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--output-stem", default="articulated_demo_room_v1"
    )
    return parser.parse_args()


def vector(text: str | None, default: tuple[float, float, float]) -> Vector:
    if not text:
        return Vector(default)
    return Vector(tuple(float(value) for value in text.split()))


def origin(element: ET.Element | None) -> tuple[Vector, Euler]:
    if element is None:
        return Vector((0.0, 0.0, 0.0)), Euler((0.0, 0.0, 0.0), "XYZ")
    return (
        vector(element.get("xyz"), (0.0, 0.0, 0.0)),
        Euler(tuple(vector(element.get("rpy"), (0.0, 0.0, 0.0))), "XYZ"),
    )


def rounded(values: Vector) -> list[float]:
    return [round(value, 6) for value in values]


def move_to_collection(
    obj: bpy.types.Object, collection: bpy.types.Collection
) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def mesh_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    if not points:
        raise RuntimeError("No mesh geometry found")
    return (
        Vector(tuple(min(point[i] for point in points) for i in range(3))),
        Vector(tuple(max(point[i] for point in points) for i in range(3))),
    )


def material_for(
    namespace: str,
    visual: ET.Element,
    cache: dict[str, bpy.types.Material],
) -> bpy.types.Material:
    material_element = visual.find("material")
    source_name = (
        material_element.get("name", "default")
        if material_element is not None
        else "default"
    )
    key = f"{namespace}::{source_name}"
    if key in cache:
        return cache[key]

    rgba = (0.5, 0.5, 0.5, 1.0)
    if material_element is not None:
        color = material_element.find("color")
        if color is not None and color.get("rgba"):
            rgba = tuple(float(value) for value in color.get("rgba").split())
    material = bpy.data.materials.new(f"Articraft::{key}")
    material.diffuse_color = rgba
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = rgba
        principled.inputs["Alpha"].default_value = rgba[3]
        principled.inputs["Roughness"].default_value = 0.38
        if "metal" in source_name or "handle" in source_name:
            principled.inputs["Metallic"].default_value = 0.65
    cache[key] = material
    return material


def create_box(
    namespace: str,
    link_name: str,
    visual: ET.Element,
    index: int,
    parent: bpy.types.Object,
    collection: bpy.types.Collection,
    material: bpy.types.Material,
) -> bpy.types.Object:
    geometry = visual.find("geometry")
    box = geometry.find("box") if geometry is not None else None
    if box is None:
        raise RuntimeError(
            f"{namespace} contains non-box geometry, which is unsupported"
        )
    location, rotation = origin(visual.find("origin"))
    visual_name = visual.get("name", f"visual_{index}")
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.object
    obj.name = f"{namespace}::{link_name}::{visual_name}"
    move_to_collection(obj, collection)
    obj.parent = parent
    obj.location = location
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = rotation
    obj.scale = vector(box.get("size"), (1.0, 1.0, 1.0))
    obj.data.materials.append(material)
    obj["asset_role"] = "articraft_visual"
    obj["asset_name"] = namespace
    obj["urdf_link"] = link_name
    return obj


def import_urdf(
    path: Path,
    namespace: str,
    label: str,
    location: Vector,
    rotation: Quaternion,
) -> dict[str, Any]:
    robot = ET.parse(path).getroot()
    collection = bpy.data.collections.new(f"Articraft {label}")
    bpy.context.scene.collection.children.link(collection)

    root = bpy.data.objects.new(f"ARTICRAFT::{namespace}", None)
    collection.objects.link(root)
    root.location = location
    root.rotation_mode = "QUATERNION"
    root.rotation_quaternion = rotation
    root["asset_role"] = "articulated_object"
    root["asset_name"] = namespace
    root["asset_label"] = label
    root["source_urdf"] = str(path)

    links: dict[str, bpy.types.Object] = {}
    for link_element in robot.findall("link"):
        link_name = link_element.get("name")
        link = bpy.data.objects.new(f"LINK::{namespace}::{link_name}", None)
        collection.objects.link(link)
        link["asset_name"] = namespace
        link["urdf_link"] = link_name
        links[link_name] = link

    child_links = {
        joint.find("child").get("link") for joint in robot.findall("joint")
    }
    root_links = [name for name in links if name not in child_links]
    if len(root_links) != 1:
        raise RuntimeError(
            f"{namespace}: expected one root link, found {root_links}"
        )
    links[root_links[0]].parent = root

    joint_report = []
    for joint_element in robot.findall("joint"):
        joint_name = joint_element.get("name")
        joint_type = joint_element.get("type")
        parent_name = joint_element.find("parent").get("link")
        child_name = joint_element.find("child").get("link")
        joint = bpy.data.objects.new(
            f"JOINT::{namespace}::{joint_name}", None
        )
        collection.objects.link(joint)
        joint.parent = links[parent_name]
        joint.location, joint.rotation_euler = origin(
            joint_element.find("origin")
        )
        joint.rotation_mode = "XYZ"
        joint["asset_name"] = namespace
        joint["asset_label"] = label
        joint["urdf_joint"] = joint_name
        joint["joint_type"] = joint_type
        axis = vector(
            (
                joint_element.find("axis").get("xyz")
                if joint_element.find("axis") is not None
                else None
            ),
            (1.0, 0.0, 0.0),
        )
        joint["axis"] = list(axis)
        limit_element = joint_element.find("limit")
        limits = {}
        if limit_element is not None:
            for key in ("lower", "upper", "effort", "velocity"):
                if limit_element.get(key) is not None:
                    value = float(limit_element.get(key))
                    limits[key] = value
                    joint[f"limit_{key}"] = value
        links[child_name].parent = joint
        joint_report.append(
            {
                "name": joint_name,
                "type": joint_type,
                "parent": parent_name,
                "child": child_name,
                "axis": rounded(axis),
                "limits": limits,
            }
        )

    materials: dict[str, bpy.types.Material] = {}
    visuals = []
    for link_element in robot.findall("link"):
        link_name = link_element.get("name")
        for index, visual in enumerate(link_element.findall("visual")):
            visuals.append(
                create_box(
                    namespace,
                    link_name,
                    visual,
                    index,
                    links[link_name],
                    collection,
                    material_for(namespace, visual, materials),
                )
            )

    bpy.context.view_layer.update()
    minimum, maximum = mesh_bounds(visuals)
    return {
        "name": namespace,
        "label": label,
        "source_urdf": str(path),
        "root_location": rounded(location),
        "root_rotation_wxyz": [
            round(rotation.w, 6),
            round(rotation.x, 6),
            round(rotation.y, 6),
            round(rotation.z, 6),
        ],
        "closed_bounds": {
            "min": rounded(minimum),
            "max": rounded(maximum),
            "dimensions": rounded(maximum - minimum),
        },
        "joint_count": len(joint_report),
        "joints": joint_report,
    }


def main() -> None:
    args = parse_args()
    paths = (
        args.source_blend,
        args.state_path,
        args.door_urdf,
        args.cabinet_urdf,
    )
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_blend = output_dir / f"{args.output_stem}.blend"
    output_glb = output_dir / f"{args.output_stem}.glb"
    output_report = output_dir / f"{args.output_stem}_assembly.json"
    state = json.loads(args.state_path.read_text())

    bpy.ops.wm.open_mainfile(filepath=str(args.source_blend.resolve()))
    floor_candidates = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH"
        and obj.dimensions.z <= 0.2
        and obj.dimensions.x * obj.dimensions.y > 10
    ]
    floor = max(
        floor_candidates, key=lambda obj: obj.dimensions.x * obj.dimensions.y
    )
    floor_min, floor_max = mesh_bounds([floor])
    floor_center = (floor_min + floor_max) * 0.5
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
    room_offset = Vector(
        (
            floor_center.x - state_center.x,
            floor_center.y - state_center.y,
            0.0,
        )
    )

    entrance = next(
        opening
        for opening in state["room_geometry"]["openings"]
        if opening["opening_type"] == "door"
    )
    door_location = (
        Vector(entrance["center_world"])
        + room_offset
        + Vector((0, 0.0875, -1.05))
    )
    cabinet_location = Vector(
        (floor_max.x - 0.26, floor_center.y + 0.65, floor_max.z)
    )
    imported = [
        import_urdf(
            args.door_urdf.resolve(),
            "entry_door",
            "Entry Door",
            door_location,
            Quaternion(),
        ),
        import_urdf(
            args.cabinet_urdf.resolve(),
            "double_door_cabinet",
            "Double-door Cabinet",
            cabinet_location,
            Quaternion((0.0, 0.0, 1.0), -math.pi / 2),
        ),
    ]

    existing_roots = [
        obj
        for obj in bpy.context.scene.objects
        if obj.get("asset_role") == "articulated_object"
        and obj.name == "ARTICRAFT::microwave"
    ]
    if len(existing_roots) != 1:
        raise RuntimeError(
            f"Expected one existing microwave, found {len(existing_roots)}"
        )
    microwave = existing_roots[0]
    microwave["asset_name"] = "microwave"
    microwave["asset_label"] = "Microwave"
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("JOINT::") and "::" not in obj.name[7:]:
            obj["asset_name"] = "microwave"
            obj["asset_label"] = "Microwave"

    all_joints = [
        obj
        for obj in bpy.context.scene.objects
        if obj.get("urdf_joint")
    ]
    bpy.context.scene["scene_type"] = "articulated_demo_room"
    bpy.context.scene["articulated_object_count"] = 3
    bpy.context.scene["articraft_joint_count"] = len(all_joints)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
    bpy.ops.export_scene.gltf(
        filepath=str(output_glb),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_extras=True,
        use_visible=True,
    )

    report = {
        "source_blend": str(args.source_blend.resolve()),
        "state_path": str(args.state_path.resolve()),
        "output_blend": str(output_blend),
        "output_glb": str(output_glb),
        "output_blend_bytes": output_blend.stat().st_size,
        "output_glb_bytes": output_glb.stat().st_size,
        "room_bounds": {
            "min": rounded(floor_min),
            "max": rounded(floor_max),
        },
        "articulated_object_count": 3,
        "total_joint_count": len(all_joints),
        "existing_microwave": {
            "name": "microwave",
            "source_urdf": microwave.get("source_urdf"),
            "joint_count": 5,
        },
        "imported_objects": imported,
    }
    output_report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
