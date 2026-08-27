#!/usr/bin/env python3
"""Export a SceneSmith floor-plan Blender file as a self-contained GLB."""

from __future__ import annotations

import argparse

from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("blend_file", type=Path)
    parser.add_argument("glb_file", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    blend_file = args.blend_file.resolve()
    glb_file = args.glb_file.resolve()

    if not blend_file.is_file():
        raise FileNotFoundError(f"Blend file not found: {blend_file}")

    glb_file.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    bpy.ops.export_scene.gltf(
        filepath=str(glb_file),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        use_visible=True,
    )

    if not glb_file.is_file() or glb_file.stat().st_size == 0:
        raise RuntimeError(f"GLB export did not produce a valid file: {glb_file}")

    print(f"Exported GLB: {glb_file}")
    print(f"Size: {glb_file.stat().st_size / (1024 * 1024):.2f} MiB")


if __name__ == "__main__":
    main()

