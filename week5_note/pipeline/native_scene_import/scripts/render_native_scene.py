#!/usr/bin/env python3
"""Render the native SceneSmith-to-MuJoCo export from several camera views."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mujoco_export" / "scene.xml"
OUTPUT_DIR = ROOT / "outputs"


def save_image(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def render_view(model: mujoco.MjModel, name: str, azimuth: float, elevation: float, distance_scale: float) -> Path:
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = model.stat.center
    camera.distance = max(float(model.stat.extent) * distance_scale, 2.5)
    camera.azimuth = azimuth
    camera.elevation = elevation

    with mujoco.Renderer(model, width=640, height=480) as renderer:
        renderer.update_scene(data, camera=camera)
        pixels = renderer.render()

    output_path = OUTPUT_DIR / f"{name}.png"
    save_image(output_path, pixels)
    return output_path


def main() -> None:
    if not SCENE_XML.exists():
        raise FileNotFoundError(f"Missing MuJoCo scene XML: {SCENE_XML}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
    views = [
        ("native_scene_diag", -45.0, -35.0, 1.25),
        ("native_scene_top", 0.0, -88.0, 1.15),
        ("native_scene_front", 0.0, -25.0, 1.20),
        ("native_scene_side", 90.0, -25.0, 1.20),
    ]

    rendered = [render_view(model, *view) for view in views]
    summary = {
        "scene_xml": str(SCENE_XML),
        "outputs": [str(path) for path in rendered],
        "nbody": int(model.nbody),
        "ngeom": int(model.ngeom),
        "nmesh": int(model.nmesh),
        "njnt": int(model.njnt),
        "nq": int(model.nq),
        "extent": float(model.stat.extent),
        "center": [float(x) for x in model.stat.center],
        "status": "rendered",
    }
    (OUTPUT_DIR / "native_scene_render_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
