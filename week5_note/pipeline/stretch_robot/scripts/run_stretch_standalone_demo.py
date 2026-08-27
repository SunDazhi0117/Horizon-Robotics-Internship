#!/usr/bin/env python3
"""Render and drive the MuJoCo Menagerie Hello Robot Stretch model."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
STRETCH_SCENE = (
    ROOT.parents[1]
    / "external"
    / "mujoco_menagerie"
    / "hello_robot_stretch"
    / "scene.xml"
)
OUTPUT_DIR = ROOT / "outputs"


def get_id(model: mujoco.MjModel, obj_type: mujoco.mjtObj, name: str) -> int:
    idx = mujoco.mj_name2id(model, obj_type, name)
    if idx < 0:
        raise KeyError(name)
    return idx


def render(model: mujoco.MjModel, data: mujoco.MjData, azimuth: float = -120.0) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = [0.0, 0.0, 0.6]
    camera.distance = 2.2
    camera.azimuth = azimuth
    camera.elevation = -25.0
    with mujoco.Renderer(model, width=640, height=480) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def save_png(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(STRETCH_SCENE))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    base_id = get_id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    forward_id = get_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "forward")
    turn_id = get_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "turn")
    lift_id = get_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "lift")
    arm_id = get_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "arm_extend")

    start_pos = data.xpos[base_id].copy()
    save_png(OUTPUT_DIR / "stretch_start.png", render(model, data))

    frames = []
    steps = int(4.0 / float(model.opt.timestep))
    for step in range(steps):
        data.ctrl[:] = 0.0
        data.ctrl[forward_id] = 0.45
        data.ctrl[turn_id] = 0.08
        data.ctrl[lift_id] = 0.18
        data.ctrl[arm_id] = 0.20
        mujoco.mj_step(model, data)
        if step % 80 == 0:
            frames.append(Image.fromarray(render(model, data)))

    final_pos = data.xpos[base_id].copy()
    save_png(OUTPUT_DIR / "stretch_final.png", render(model, data))
    gif_path = OUTPUT_DIR / "stretch_motion.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=83, loop=0)

    summary = {
        "source_scene": str(STRETCH_SCENE),
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nu": int(model.nu),
        "nmesh": int(model.nmesh),
        "actuators": [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
            for i in range(model.nu)
        ],
        "start_pos": [float(x) for x in start_pos],
        "final_pos": [float(x) for x in final_pos],
        "moved_distance_xy": float(np.linalg.norm(final_pos[:2] - start_pos[:2])),
        "all_finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "contact_count_final": int(data.ncon),
        "outputs": {
            "start_png": str(OUTPUT_DIR / "stretch_start.png"),
            "final_png": str(OUTPUT_DIR / "stretch_final.png"),
            "motion_gif": str(gif_path),
        },
        "passed": bool(np.linalg.norm(final_pos[:2] - start_pos[:2]) > 0.1),
        "note": "Standalone Stretch load and actuator smoke test.",
    }
    (OUTPUT_DIR / "stretch_standalone_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
