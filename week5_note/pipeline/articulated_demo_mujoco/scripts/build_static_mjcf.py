#!/usr/bin/env python3
"""Build a static MuJoCo MJCF from the articulated demo room GLB.

This preserves the GLB nodes as separate mesh files, but it does not recreate
the articulated joints. The goal is to test whether the full complex scene can
be loaded and rendered by MuJoCo.
"""

from __future__ import annotations

import json
import re
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
OUTPUT_XML = XML_DIR / "articulated_demo_static.xml"
SUMMARY_PATH = ROOT / "outputs" / "build_summary.json"


AXIS_CONVERSION = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)


def safe_name(value: str, index: int) -> str:
    value = value.replace("::", "_")
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = "mesh"
    return f"{index:03d}_{value[:80]}"


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


def export_meshes(scene: trimesh.Scene) -> list[dict[str, object]]:
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
    ground_shift = np.eye(4)
    ground_shift[2, 3] = -min_z

    exported = []
    MESH_DIR.mkdir(parents=True, exist_ok=True)
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
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
            }
        )
    return exported


def build_xml(exported: list[dict[str, object]]) -> None:
    mujoco = ET.Element("mujoco", {"model": "articulated_demo_room_static"})
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
        file_name = Path(str(item["file"])).name
        ET.SubElement(asset, "mesh", {"name": str(item["mesh_name"]), "file": file_name})

    worldbody = ET.SubElement(mujoco, "worldbody")
    ET.SubElement(worldbody, "light", {"name": "top", "pos": "2 2 6", "dir": "0 0 -1"})
    ET.SubElement(
        worldbody,
        "camera",
        {
            "name": "overview",
            "pos": "2.0 -7.5 5.0",
            "xyaxes": "1 0 0 0 0.58 0.82",
        },
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

    room = ET.SubElement(worldbody, "body", {"name": "articulated_demo_room_static"})
    for item in exported:
        ET.SubElement(
            room,
            "geom",
            {
                "name": str(item["mesh_name"]),
                "type": "mesh",
                "mesh": str(item["mesh_name"]),
                "rgba": "0.82 0.80 0.74 1",
            },
        )

    indent(mujoco)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(mujoco)
    tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)


def main() -> None:
    if not SOURCE_GLB.exists():
        raise FileNotFoundError(SOURCE_GLB)

    scene = trimesh.load(SOURCE_GLB, force="scene")
    exported = export_meshes(scene)
    build_xml(exported)

    all_bounds = np.array([item["bounds"] for item in exported], dtype=float)
    summary = {
        "source_glb": str(SOURCE_GLB),
        "output_xml": str(OUTPUT_XML),
        "mesh_count": len(exported),
        "node_count": len(scene.graph.nodes_geometry),
        "geometry_count": len(scene.geometry),
        "combined_bounds": {
            "min": all_bounds[:, 0, :].min(axis=0).tolist(),
            "max": all_bounds[:, 1, :].max(axis=0).tolist(),
        },
        "note": "Static MuJoCo import only; original GLB articulation metadata is not converted into MJCF joints.",
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
