#!/usr/bin/env python3
"""Build a MuJoCo MJCF with reconstructed joints for the articulated demo room.

The source GLB stores articulation metadata in node extras. This script keeps
the already exported world-space OBJ meshes and groups selected meshes under
MuJoCo bodies with hinge/slide joints. It is a first-pass articulation rebuild:
good enough to prove MuJoCo joint loading and motion, not yet a full URDF-grade
physics conversion.
"""

from __future__ import annotations

import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
SOURCE_GLB = Path(
    "/home/users/dazhi.sun-labs/projects/scenesmith/outputs/2026-07-01/"
    "articulated_demo_room_v1/articulated_demo_room_v1.glb"
)
MESH_DIR = ROOT / "assets" / "meshes"
XML_DIR = ROOT / "xml"
OUTPUT_XML = XML_DIR / "articulated_demo_with_joints.xml"
SUMMARY_PATH = ROOT / "outputs" / "joint_build_summary.json"

AXIS_CONVERSION = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)


MOVING_GROUPS = {
    "entry_door": {
        "prefix": "entry_door::door::",
        "joint": "frame_to_door",
        "source_joint": "frame_to_door",
        "type": "hinge",
        "axis": "0 0 1",
        "range": "0 1.5708",
    },
    "cabinet_left_door": {
        "prefix": "double_door_cabinet::left_door::",
        "joint": "left_hinge",
        "source_joint": "left_hinge",
        "type": "hinge",
        "axis": "0 0 -1",
        "range": "0 1.5708",
    },
    "cabinet_right_door": {
        "prefix": "double_door_cabinet::right_door::",
        "joint": "right_hinge",
        "source_joint": "right_hinge",
        "type": "hinge",
        "axis": "0 0 1",
        "range": "0 1.5708",
    },
    "microwave_door": {
        "prefix": "microwave::front_door::",
        "joint": "body_to_front_door",
        "source_joint": "body_to_front_door",
        "type": "hinge",
        "axis": "0 0 1",
        "range": "0 1.75",
    },
    "microwave_tray": {
        "prefix": "microwave::sliding_tray::",
        "joint": "body_to_sliding_tray",
        "source_joint": "body_to_sliding_tray",
        "type": "slide",
        "axis": "0 -1 0",
        "range": "0 0.22",
    },
    "microwave_turntable": {
        "prefix": "microwave::turntable::",
        "joint": "tray_to_turntable",
        "source_joint": "tray_to_turntable",
        "type": "hinge",
        "axis": "0 0 1",
        "range": None,
    },
    "microwave_upper_knob": {
        "prefix": "microwave::upper_knob::",
        "joint": "body_to_upper_knob",
        "source_joint": "body_to_upper_knob",
        "type": "hinge",
        "axis": "0 1 0",
        "range": None,
    },
    "microwave_lower_knob": {
        "prefix": "microwave::lower_knob::",
        "joint": "body_to_lower_knob",
        "source_joint": "body_to_lower_knob",
        "type": "hinge",
        "axis": "0 1 0",
        "range": None,
    },
}


def safe_name(value: str, index: int) -> str:
    value = value.replace("::", "_")
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return f"{index:03d}_{value[:80] or 'mesh'}"


def quat_to_matrix(quat: list[float]) -> np.ndarray:
    x, y, z, w = quat
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array(
        [
            [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
            [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
            [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
        ],
        dtype=float,
    )


def local_matrix(node: dict[str, object]) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T

    matrix = np.eye(4)
    if "translation" in node:
        matrix[:3, 3] = np.array(node["translation"], dtype=float)
    if "rotation" in node:
        rotation = np.eye(4)
        rotation[:3, :3] = quat_to_matrix(node["rotation"])
        matrix = matrix @ rotation
    if "scale" in node:
        scale = np.eye(4)
        scale[:3, :3] = np.diag(np.array(node["scale"], dtype=float))
        matrix = matrix @ scale
    return matrix


def load_gltf_json(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    offset = 12
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            return json.loads(chunk.decode("utf-8"))
    raise RuntimeError(f"No JSON chunk found in {path}")


def global_matrices(gltf: dict[str, object]) -> list[np.ndarray]:
    nodes = gltf["nodes"]
    parents: dict[int, int] = {}
    for parent_index, node in enumerate(nodes):
        for child_index in node.get("children", []):
            parents[child_index] = parent_index

    matrices = []
    for index in range(len(nodes)):
        chain = []
        cursor = index
        while cursor is not None:
            chain.append(cursor)
            cursor = parents.get(cursor)
        matrix = np.eye(4)
        for node_index in reversed(chain):
            matrix = matrix @ local_matrix(nodes[node_index])
        matrices.append(matrix)
    return matrices


def export_world_meshes(scene: trimesh.Scene) -> tuple[list[dict[str, object]], float]:
    raw_meshes = []
    for index, node_name in enumerate(sorted(scene.graph.nodes_geometry)):
        transform, geometry_name = scene.graph.get(node_name)
        geometry = scene.geometry[geometry_name]
        if not isinstance(geometry, trimesh.Trimesh) or geometry.vertices.size == 0:
            continue
        mesh = geometry.copy()
        mesh.apply_transform(AXIS_CONVERSION @ transform)
        raw_meshes.append((index, node_name, geometry_name, mesh))

    if not raw_meshes:
        raise RuntimeError(f"No mesh nodes found in {SOURCE_GLB}")

    min_z = min(float(mesh.bounds[0][2]) for _, _, _, mesh in raw_meshes)
    ground_shift_z = -min_z
    ground_shift = np.eye(4)
    ground_shift[2, 3] = ground_shift_z

    MESH_DIR.mkdir(parents=True, exist_ok=True)
    exported = []
    for index, node_name, geometry_name, mesh in raw_meshes:
        mesh.apply_transform(ground_shift)
        mesh_name = safe_name(node_name, index)
        mesh_path = MESH_DIR / f"{mesh_name}.obj"
        mesh.export(mesh_path)
        exported.append(
            {
                "node": node_name,
                "geometry": geometry_name,
                "mesh_name": mesh_name,
                "file": str(mesh_path),
                "bounds": mesh.bounds.tolist(),
            }
        )
    return exported, ground_shift_z


def find_joint_pivots(gltf: dict[str, object], ground_shift_z: float) -> dict[str, list[float]]:
    matrices = global_matrices(gltf)
    pivots = {}
    for index, node in enumerate(gltf["nodes"]):
        extras = node.get("extras", {})
        joint_name = extras.get("urdf_joint")
        if not joint_name:
            continue
        position = (AXIS_CONVERSION @ matrices[index])[:3, 3]
        position[2] += ground_shift_z
        pivots[joint_name] = [float(v) for v in position]
    return pivots


def group_for_node(node_name: str) -> str | None:
    for group_name, config in MOVING_GROUPS.items():
        if node_name.startswith(config["prefix"]):
            return group_name
    return None


def indent(element: ET.Element, level: int = 0) -> None:
    pad = "\n" + level * "  "
    if len(element):
        if not element.text or not element.text.strip():
            element.text = pad + "  "
        for child in element:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = pad
    if level and (not element.tail or not element.tail.strip()):
        element.tail = pad


def add_geom(parent: ET.Element, item: dict[str, object], pivot: list[float] | None = None) -> None:
    attrs = {
        "name": str(item["mesh_name"]),
        "type": "mesh",
        "mesh": str(item["mesh_name"]),
        "rgba": "0.82 0.80 0.74 1",
        "contype": "0",
        "conaffinity": "0",
    }
    if pivot is not None:
        attrs["pos"] = f"{-pivot[0]:.6f} {-pivot[1]:.6f} {-pivot[2]:.6f}"
    ET.SubElement(parent, "geom", attrs)


def build_xml(exported: list[dict[str, object]], pivots: dict[str, list[float]]) -> None:
    mujoco = ET.Element("mujoco", {"model": "articulated_demo_room_with_joints"})
    ET.SubElement(
        mujoco,
        "compiler",
        {"angle": "radian", "meshdir": "../assets/meshes", "autolimits": "true"},
    )
    ET.SubElement(mujoco, "option", {"gravity": "0 0 -9.81", "timestep": "0.002"})
    visual = ET.SubElement(mujoco, "visual")
    ET.SubElement(visual, "global", {"offwidth": "1000", "offheight": "760"})

    asset = ET.SubElement(mujoco, "asset")
    for item in exported:
        ET.SubElement(asset, "mesh", {"name": str(item["mesh_name"]), "file": Path(str(item["file"])).name})

    worldbody = ET.SubElement(mujoco, "worldbody")
    ET.SubElement(worldbody, "light", {"name": "top", "pos": "2 2 6", "dir": "0 0 -1"})
    ET.SubElement(
        worldbody,
        "camera",
        {"name": "overview", "pos": "2.0 -7.5 5.0", "xyaxes": "1 0 0 0 0.58 0.82"},
    )
    ET.SubElement(
        worldbody,
        "geom",
        {
            "name": "reference_ground",
            "type": "plane",
            "size": "6 6 0.02",
            "rgba": "0.18 0.22 0.25 1",
            "contype": "0",
            "conaffinity": "0",
        },
    )

    static_body = ET.SubElement(worldbody, "body", {"name": "static_room_shell"})
    grouped: dict[str, list[dict[str, object]]] = {name: [] for name in MOVING_GROUPS}
    for item in exported:
        group_name = group_for_node(str(item["node"]))
        if group_name is None:
            add_geom(static_body, item)
        else:
            grouped[group_name].append(item)

    for group_name, items in grouped.items():
        if not items:
            continue
        config = MOVING_GROUPS[group_name]
        joint_name = config["joint"]
        pivot = pivots[config["source_joint"]]
        body = ET.SubElement(
            worldbody,
            "body",
            {"name": group_name, "pos": f"{pivot[0]:.6f} {pivot[1]:.6f} {pivot[2]:.6f}"},
        )
        ET.SubElement(body, "inertial", {"pos": "0 0 0", "mass": "1", "diaginertia": "0.01 0.01 0.01"})
        joint_attrs = {
            "name": joint_name,
            "type": config["type"],
            "axis": config["axis"],
            "damping": "0.1",
        }
        if config["range"] is not None:
            joint_attrs["range"] = config["range"]
        ET.SubElement(body, "joint", joint_attrs)
        for item in items:
            add_geom(body, item, pivot)

    indent(mujoco)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(mujoco).write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)


def main() -> None:
    scene = trimesh.load(SOURCE_GLB, force="scene")
    gltf = load_gltf_json(SOURCE_GLB)
    exported, ground_shift_z = export_world_meshes(scene)
    pivots = find_joint_pivots(gltf, ground_shift_z)
    build_xml(exported, pivots)

    summary = {
        "source_glb": str(SOURCE_GLB),
        "output_xml": str(OUTPUT_XML),
        "mesh_count": len(exported),
        "joint_count_expected": len(MOVING_GROUPS),
        "joints": {
            config["joint"]: {
                "body": group_name,
                "type": config["type"],
                "axis": config["axis"],
                "range": config["range"],
                "pivot": pivots[config["source_joint"]],
            }
            for group_name, config in MOVING_GROUPS.items()
        },
        "note": "First-pass MuJoCo articulation rebuild from GLB mesh groups and joint metadata.",
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
