#!/usr/bin/env python3
"""Render a MuJoCo joint demo for the articulated demo room."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "xml" / "articulated_demo_with_joints.xml"
OUTPUT_DIR = ROOT / "outputs"

OPEN_TARGETS = {
    "frame_to_door": 1.2,
    "left_hinge": 1.2,
    "right_hinge": 1.2,
    "body_to_front_door": 1.25,
    "body_to_sliding_tray": 0.18,
    "tray_to_turntable": 2.4,
    "body_to_upper_knob": 1.2,
    "body_to_lower_knob": -1.2,
}


def set_qpos(model: mujoco.MjModel, data: mujoco.MjData, targets: dict[str, float]) -> None:
    data.qpos[:] = 0.0
    for joint_name, value in targets.items():
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if joint_id < 0:
            raise KeyError(joint_name)
        qpos_index = model.jnt_qposadr[joint_id]
        data.qpos[qpos_index] = value
    mujoco.mj_forward(model, data)


def render(model: mujoco.MjModel, data: mujoco.MjData, azimuth: float, elevation: float, distance_scale: float) -> np.ndarray:
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


def interpolate_targets(alpha: float) -> dict[str, float]:
    return {name: alpha * value for name, value in OPEN_TARGETS.items()}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
    data = mujoco.MjData(model)

    set_qpos(model, data, {})
    closed_top = OUTPUT_DIR / "articulated_joints_closed_top.png"
    closed_diag = OUTPUT_DIR / "articulated_joints_closed_diag.png"
    save_png(closed_top, render(model, data, 0.0, -88.0, 0.72))
    save_png(closed_diag, render(model, data, -45.0, -32.0, 1.0))

    set_qpos(model, data, OPEN_TARGETS)
    open_top = OUTPUT_DIR / "articulated_joints_open_top.png"
    open_diag = OUTPUT_DIR / "articulated_joints_open_diag.png"
    save_png(open_top, render(model, data, 0.0, -88.0, 0.72))
    save_png(open_diag, render(model, data, -45.0, -32.0, 1.0))

    frames = []
    for alpha in np.concatenate([np.linspace(0.0, 1.0, 36), np.linspace(1.0, 0.0, 36)]):
        set_qpos(model, data, interpolate_targets(float(alpha)))
        frames.append(Image.fromarray(render(model, data, 0.0, -88.0, 0.72)))
    gif_path = OUTPUT_DIR / "articulated_joints_motion.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=83, loop=0)

    joint_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        for i in range(model.njnt)
    ]
    summary = {
        "scene_xml": str(SCENE_XML),
        "joint_count": int(model.njnt),
        "qpos_count": int(model.nq),
        "joints": joint_names,
        "open_targets": OPEN_TARGETS,
        "outputs": [
            str(closed_top),
            str(closed_diag),
            str(open_top),
            str(open_diag),
            str(gif_path),
        ],
        "status": "rendered_joint_demo",
        "note": "First-pass kinematic joint visualization; not robot control yet.",
    }
    summary_path = OUTPUT_DIR / "joint_render_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
