#!/usr/bin/env python3
"""Place an Articraft URDF microwave on a SceneSmith desk and export GLB."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET

from itertools import product
from pathlib import Path
from typing import Any

import bpy

from mathutils import Euler, Quaternion, Vector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene_dir", type=Path)
    parser.add_argument("microwave_urdf", type=Path)
    parser.add_argument("--source-blend", type=Path)
    parser.add_argument("--state-path", type=Path)
    parser.add_argument("--desk-id", default="writing_desk_0")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--output-stem", default="static_reading_room_with_microwave"
    )
    return parser.parse_args()


def vector(text: str | None, default: tuple[float, float, float]) -> Vector:
    if not text:
        return Vector(default)
    return Vector(tuple(float(value) for value in text.split()))


def origin(element: ET.Element | None) -> tuple[Vector, Euler]:
    if element is None:
        return Vector((0.0, 0.0, 0.0)), Euler((0.0, 0.0, 0.0), "XYZ")
    xyz = vector(element.get("xyz"), (0.0, 0.0, 0.0))
    rpy = vector(element.get("rpy"), (0.0, 0.0, 0.0))
    return xyz, Euler(tuple(rpy), "XYZ")


def move_to_collection(
    obj: bpy.types.Object, collection: bpy.types.Collection
) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def material_for(
    visual: ET.Element, cache: dict[str, bpy.types.Material]
) -> bpy.types.Material:
    material_element = visual.find("material")
    name = (
        material_element.get("name", "articraft_default")
        if material_element is not None
        else "articraft_default"
    )
    if name in cache:
        return cache[name]

    rgba = (0.5, 0.5, 0.5, 1.0)
    if material_element is not None:
        color = material_element.find("color")
        if color is not None and color.get("rgba"):
            rgba = tuple(float(value) for value in color.get("rgba").split())

    material = bpy.data.materials.new(f"Articraft::{name}")
    material.diffuse_color = rgba
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = rgba
        principled.inputs["Alpha"].default_value = rgba[3]
        principled.inputs["Roughness"].default_value = 0.35
        if "metal" in name:
            principled.inputs["Metallic"].default_value = 0.7
    cache[name] = material
    return material


def create_box(
    name: str,
    size: Vector,
    location: Vector,
    rotation: Euler,
    parent: bpy.types.Object,
    collection: bpy.types.Collection,
    material: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, collection)
    obj.parent = parent
    obj.location = location
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = rotation
    obj.scale = size
    obj.data.materials.append(material)
    obj["asset_role"] = "articraft_microwave_visual"
    return obj


def mesh_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    if not points:
        raise RuntimeError("No microwave mesh geometry was created")
    return (
        Vector(tuple(min(point[i] for point in points) for i in range(3))),
        Vector(tuple(max(point[i] for point in points) for i in range(3))),
    )


def state_object_world_bounds(
    data: dict[str, Any], room_offset: Vector
) -> tuple[Vector, Vector]:
    translation = Vector(data["transform"]["translation"]) + room_offset
    wxyz = data["transform"]["rotation_wxyz"]
    rotation = Quaternion((wxyz[0], wxyz[1], wxyz[2], wxyz[3]))
    corners = [
        translation + rotation @ Vector((x, y, z))
        for x, y, z in product(
            (data["bbox_min"][0], data["bbox_max"][0]),
            (data["bbox_min"][1], data["bbox_max"][1]),
            (data["bbox_min"][2], data["bbox_max"][2]),
        )
    ]
    return (
        Vector(tuple(min(point[i] for point in corners) for i in range(3))),
        Vector(tuple(max(point[i] for point in corners) for i in range(3))),
    )


def rounded(values: Vector) -> list[float]:
    return [round(value, 6) for value in values]


def main() -> None:
    args = parse_args()
    scene_dir = args.scene_dir.resolve()
    urdf_path = args.microwave_urdf.resolve()
    source_blend = (
        args.source_blend.resolve()
        if args.source_blend
        else scene_dir / "static_reading_room.blend"
    )
    state_path = (
        args.state_path.resolve()
        if args.state_path
        else (
            scene_dir
            / "room_living_room/scene_states/scene_after_furniture/scene_state.json"
        )
    )
    output_dir = args.output_dir.resolve() if args.output_dir else scene_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_blend = output_dir / f"{args.output_stem}.blend"
    output_glb = output_dir / f"{args.output_stem}.glb"
    report_path = output_dir / f"{args.output_stem}_placement_report.json"
    for path in (source_blend, state_path, urdf_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    state = json.loads(state_path.read_text())
    desk = state["objects"][args.desk_id]
    tree = ET.parse(urdf_path)
    robot = tree.getroot()

    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    room_objects = list(bpy.context.scene.objects)
    floor_candidates = [
        obj
        for obj in room_objects
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
    desk_min, desk_max = state_object_world_bounds(desk, room_offset)
    desk_center = (desk_min + desk_max) * 0.5
    desk_wxyz = desk["transform"]["rotation_wxyz"]
    desk_rotation = Quaternion(
        (desk_wxyz[0], desk_wxyz[1], desk_wxyz[2], desk_wxyz[3])
    )
    desk_front = desk_rotation @ Vector((0.0, 1.0, 0.0))
    microwave_rotation = desk_rotation @ Quaternion(
        (0.0, 0.0, 1.0), 3.141592653589793
    )

    collection = bpy.data.collections.new("Articraft Microwave")
    bpy.context.scene.collection.children.link(collection)
    root = bpy.data.objects.new("ARTICRAFT::microwave", None)
    collection.objects.link(root)
    root.location = (
        Vector((desk_center.x, desk_center.y, desk_max.z))
        - desk_front * 0.04
    )
    root.rotation_mode = "QUATERNION"
    root.rotation_quaternion = microwave_rotation
    root["asset_role"] = "articulated_object"
    root["source_urdf"] = str(urdf_path)
    root["support_object"] = args.desk_id

    links: dict[str, bpy.types.Object] = {}
    for link_element in robot.findall("link"):
        link_name = link_element.get("name")
        link_obj = bpy.data.objects.new(f"LINK::{link_name}", None)
        collection.objects.link(link_obj)
        link_obj["urdf_link"] = link_name
        links[link_name] = link_obj

    child_links = {
        joint.find("child").get("link") for joint in robot.findall("joint")
    }
    root_links = [name for name in links if name not in child_links]
    if len(root_links) != 1:
        raise RuntimeError(f"Expected one URDF root link, found {root_links}")
    links[root_links[0]].parent = root

    joint_report = []
    for joint in robot.findall("joint"):
        name = joint.get("name")
        joint_type = joint.get("type")
        parent_name = joint.find("parent").get("link")
        child_name = joint.find("child").get("link")
        joint_obj = bpy.data.objects.new(f"JOINT::{name}", None)
        collection.objects.link(joint_obj)
        joint_obj.parent = links[parent_name]
        joint_obj.location, joint_obj.rotation_euler = origin(joint.find("origin"))
        joint_obj.rotation_mode = "XYZ"
        joint_obj["urdf_joint"] = name
        joint_obj["joint_type"] = joint_type

        axis = vector(
            joint.find("axis").get("xyz")
            if joint.find("axis") is not None
            else None,
            (1.0, 0.0, 0.0),
        )
        joint_obj["axis"] = list(axis)
        limit = joint.find("limit")
        limits = {}
        if limit is not None:
            for key in ("lower", "upper", "effort", "velocity"):
                if limit.get(key) is not None:
                    limits[key] = float(limit.get(key))
                    joint_obj[f"limit_{key}"] = limits[key]

        links[child_name].parent = joint_obj
        joint_report.append(
            {
                "name": name,
                "type": joint_type,
                "parent": parent_name,
                "child": child_name,
                "axis": rounded(axis),
                "limits": limits,
            }
        )

    materials: dict[str, bpy.types.Material] = {}
    visual_objects = []
    for link_element in robot.findall("link"):
        link_name = link_element.get("name")
        for index, visual in enumerate(link_element.findall("visual")):
            geometry = visual.find("geometry")
            box = geometry.find("box") if geometry is not None else None
            if box is None:
                raise RuntimeError("Only box URDF geometry is supported")
            size = vector(box.get("size"), (1.0, 1.0, 1.0))
            location, rotation = origin(visual.find("origin"))
            visual_name = visual.get("name", f"visual_{index}")
            visual_objects.append(
                create_box(
                    name=f"microwave::{link_name}::{visual_name}",
                    size=size,
                    location=location,
                    rotation=rotation,
                    parent=links[link_name],
                    collection=collection,
                    material=material_for(visual, materials),
                )
            )

    bpy.context.view_layer.update()
    microwave_min, microwave_max = mesh_bounds(visual_objects)
    base_clearance = microwave_min.z - desk_max.z
    support_fit = (
        microwave_min.x >= desk_min.x
        and microwave_max.x <= desk_max.x
        and microwave_min.y >= desk_min.y
        and microwave_max.y <= desk_max.y
    )
    if abs(base_clearance) > 0.002:
        raise RuntimeError(
            f"Microwave is not seated on desk: clearance={base_clearance}"
        )
    if not support_fit:
        raise RuntimeError("Microwave footprint extends beyond the writing desk")

    bpy.context.scene["scene_type"] = "static_reading_room_with_articraft_microwave"
    bpy.context.scene["articraft_joint_count"] = len(joint_report)
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
        "source_scene": str(source_blend),
        "source_urdf": str(urdf_path),
        "output_blend": str(output_blend),
        "output_glb": str(output_glb),
        "output_blend_bytes": output_blend.stat().st_size,
        "output_glb_bytes": output_glb.stat().st_size,
        "support_object": args.desk_id,
        "desk_front": rounded(desk_front),
        "microwave_root_rotation_wxyz": [
            round(microwave_rotation.w, 6),
            round(microwave_rotation.x, 6),
            round(microwave_rotation.y, 6),
            round(microwave_rotation.z, 6),
        ],
        "desk_bounds": {"min": rounded(desk_min), "max": rounded(desk_max)},
        "microwave_bounds": {
            "min": rounded(microwave_min),
            "max": rounded(microwave_max),
            "dimensions": rounded(microwave_max - microwave_min),
        },
        "base_clearance_m": round(base_clearance, 6),
        "footprint_inside_desk": support_fit,
        "joint_count": len(joint_report),
        "joints": joint_report,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
