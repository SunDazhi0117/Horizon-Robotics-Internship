#!/usr/bin/env python
"""Render the Phase 1 static SceneSmith mesh in MuJoCo."""

from __future__ import annotations

import json
import os

from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np

from PIL import Image


ROOT = Path("/home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import")
XML_PATH = ROOT / "xml/scene_only.xml"
OUTPUT_IMAGE = ROOT / "outputs/scene_render.png"
SUMMARY_JSON = ROOT / "outputs/scene_render_summary.json"


def render_scene() -> dict:
    model = mujoco.MjModel.from_xml_path(str(XML_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = model.stat.center
    camera.distance = max(model.stat.extent * 0.65, 2.0)
    camera.azimuth = 135
    camera.elevation = -35

    with mujoco.Renderer(model, height=600, width=800) as renderer:
        renderer.update_scene(data, camera=camera)
        pixels = renderer.render()

    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(OUTPUT_IMAGE)

    gray = pixels.astype(np.float32).mean(axis=2)
    non_empty = bool(gray.std() > 1.0 and gray.mean() > 1.0)
    summary = {
        "xml_path": str(XML_PATH),
        "output_image": str(OUTPUT_IMAGE),
        "image_shape": list(pixels.shape),
        "image_mean": float(gray.mean()),
        "image_std": float(gray.std()),
        "non_empty_image": non_empty,
        "model_stats": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
            "nu": int(model.nu),
        },
        "model_center": [float(v) for v in model.stat.center],
        "model_extent": float(model.stat.extent),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    summary = render_scene()
    print("=== Week5 MuJoCo Phase 1 Render ===")
    print(f"xml:          {summary['xml_path']}")
    print(f"image:        {summary['output_image']}")
    print(f"bodies:       {summary['model_stats']['nbody']}")
    print(f"joints:       {summary['model_stats']['njnt']}")
    print(f"geoms:        {summary['model_stats']['ngeom']}")
    print(f"meshes:       {summary['model_stats']['nmesh']}")
    print(f"image mean:   {summary['image_mean']:.2f}")
    print(f"image std:    {summary['image_std']:.2f}")
    print(f"non-empty:    {summary['non_empty_image']}")
    if not summary["non_empty_image"]:
        raise SystemExit("Rendered image appears blank.")


if __name__ == "__main__":
    main()
