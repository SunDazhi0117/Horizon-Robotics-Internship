#!/usr/bin/env python3
"""Render the static MuJoCo import of the articulated demo room."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "xml" / "articulated_demo_static.xml"
OUTPUT_DIR = ROOT / "outputs"


def render(model: mujoco.MjModel, azimuth: float, elevation: float, distance_scale: float) -> np.ndarray:
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = model.stat.center
    camera.distance = max(float(model.stat.extent) * distance_scale, 3.0)
    camera.azimuth = azimuth
    camera.elevation = elevation

    with mujoco.Renderer(model, width=1000, height=760) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def save_png(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def main() -> None:
    if not SCENE_XML.exists():
        raise FileNotFoundError(SCENE_XML)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE_XML))

    views = {
        "articulated_demo_diag": (-45.0, -32.0, 1.0),
        "articulated_demo_top": (0.0, -88.0, 0.72),
        "articulated_demo_side": (90.0, -25.0, 0.88),
        "articulated_demo_front": (0.0, -25.0, 0.88),
    }
    png_paths = []
    for name, view in views.items():
        pixels = render(model, *view)
        path = OUTPUT_DIR / f"{name}.png"
        save_png(path, pixels)
        png_paths.append(path)

    frames = []
    for azimuth in np.linspace(-180.0, 180.0, 48, endpoint=False):
        frames.append(Image.fromarray(render(model, float(azimuth), -35.0, 0.95)))
    gif_path = OUTPUT_DIR / "articulated_demo_static_turntable.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=83,
        loop=0,
    )

    summary = {
        "scene_xml": str(SCENE_XML),
        "png_outputs": [str(path) for path in png_paths],
        "gif_output": str(gif_path),
        "nbody": int(model.nbody),
        "ngeom": int(model.ngeom),
        "nmesh": int(model.nmesh),
        "njnt": int(model.njnt),
        "nq": int(model.nq),
        "extent": float(model.stat.extent),
        "center": [float(x) for x in model.stat.center],
        "status": "rendered_static_scene",
    }
    summary_path = OUTPUT_DIR / "render_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
