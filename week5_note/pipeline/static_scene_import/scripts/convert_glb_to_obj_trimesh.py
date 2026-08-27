#!/usr/bin/env python
"""Convert the selected SceneSmith GLB into a single static OBJ with trimesh."""

from __future__ import annotations

from pathlib import Path

import trimesh


ROOT = Path("/home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import")
SOURCE_GLB = Path(
    "/home/users/dazhi.sun-labs/projects/scenesmith/"
    "outputs/2026-07-03/19-02-49/scene_000/simple_study_room.glb"
)
OUTPUT_OBJ = ROOT / "assets/simple_study_room.obj"


def main() -> None:
    if not SOURCE_GLB.is_file():
        raise FileNotFoundError(SOURCE_GLB)

    loaded = trimesh.load(SOURCE_GLB, force="scene")
    meshes = []

    if isinstance(loaded, trimesh.Trimesh):
        meshes = [loaded]
    else:
        for node_name in loaded.graph.nodes_geometry:
            transform, geometry_name = loaded.graph[node_name]
            geometry = loaded.geometry[geometry_name]
            if not isinstance(geometry, trimesh.Trimesh):
                continue
            mesh = geometry.copy()
            mesh.apply_transform(transform)
            meshes.append(mesh)

    if not meshes:
        raise RuntimeError(f"No mesh geometry found in {SOURCE_GLB}")

    combined = trimesh.util.concatenate(meshes)
    OUTPUT_OBJ.parent.mkdir(parents=True, exist_ok=True)
    combined.export(OUTPUT_OBJ)

    print(f"source_glb={SOURCE_GLB}")
    print(f"output_obj={OUTPUT_OBJ}")
    print(f"mesh_count={len(meshes)}")
    print(f"vertices={len(combined.vertices)}")
    print(f"faces={len(combined.faces)}")


if __name__ == "__main__":
    main()
