#!/usr/bin/env python3
"""Drive a minimal mobile base in the articulated demo room."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "xml" / "articulated_demo_with_mobile_base.xml"
OUTPUT_DIR = ROOT / "outputs"

ROBOT_TARGETS = {
    "base_x_pos": 0.75,
    "base_y_pos": 0.35,
    "base_yaw_pos": 0.7,
}


def obj_id(model: mujoco.MjModel, obj_type: mujoco.mjtObj, name: str) -> int:
    idx = mujoco.mj_name2id(model, obj_type, name)
    if idx < 0:
        raise KeyError(name)
    return idx


def render(model: mujoco.MjModel, data: mujoco.MjData) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = model.stat.center
    camera.distance = max(float(model.stat.extent) * 0.72, 3.0)
    camera.azimuth = 0.0
    camera.elevation = -88.0
    with mujoco.Renderer(model, width=1000, height=760) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def set_ctrl(model: mujoco.MjModel, data: mujoco.MjData, alpha: float) -> None:
    data.ctrl[:] = 0.0
    for name, target in ROBOT_TARGETS.items():
        data.ctrl[obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)] = alpha * target


def save(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)

    save(OUTPUT_DIR / "mobile_base_start.png", render(model, data))
    body_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "simple_mobile_base")
    start_pos = data.xpos[body_id].copy()
    frames = []

    steps = int(4.0 / float(model.opt.timestep))
    for step in range(steps):
        alpha = min(1.0, data.time / 2.0)
        set_ctrl(model, data, alpha)
        mujoco.mj_step(model, data)
        if step % 80 == 0:
            frames.append(Image.fromarray(render(model, data)))

    final_pos = data.xpos[body_id].copy()
    save(OUTPUT_DIR / "mobile_base_final.png", render(model, data))

    gif_path = OUTPUT_DIR / "mobile_base_motion.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=83, loop=0)

    moved_distance = float(np.linalg.norm(final_pos[:2] - start_pos[:2]))
    summary = {
        "scene_xml": str(SCENE_XML),
        "robot": "simple_mobile_base",
        "start_pos": [float(x) for x in start_pos],
        "final_pos": [float(x) for x in final_pos],
        "moved_distance_xy": moved_distance,
        "all_finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "contact_count_final": int(data.ncon),
        "outputs": {
            "start_png": str(OUTPUT_DIR / "mobile_base_start.png"),
            "final_png": str(OUTPUT_DIR / "mobile_base_final.png"),
            "motion_gif": str(gif_path),
        },
        "passed": bool(moved_distance > 0.5 and np.isfinite(data.qpos).all()),
        "note": "Minimal mobile-base loading and motion smoke test; not a real robot task.",
    }
    (OUTPUT_DIR / "mobile_base_demo_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
