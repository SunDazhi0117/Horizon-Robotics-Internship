#!/usr/bin/env python3
"""Drive reconstructed joints with MuJoCo actuators and validate simple tasks."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "xml" / "articulated_demo_with_actuators.xml"
OUTPUT_DIR = ROOT / "outputs"

ACTUATOR_TARGETS = {
    "frame_to_door_pos": 1.2,
    "left_hinge_pos": 1.2,
    "right_hinge_pos": 1.2,
    "body_to_front_door_pos": 1.25,
    "body_to_sliding_tray_pos": 0.18,
    "tray_to_turntable_pos": 2.4,
    "body_to_upper_knob_pos": 1.2,
    "body_to_lower_knob_pos": -1.2,
}

TASKS = {
    "open_entry_door": ("frame_to_door", 1.0),
    "open_left_cabinet_door": ("left_hinge", 1.0),
    "open_right_cabinet_door": ("right_hinge", 1.0),
    "open_microwave_door": ("body_to_front_door", 1.0),
    "extend_microwave_tray": ("body_to_sliding_tray", 0.14),
}


def name_to_actuator_id(model: mujoco.MjModel, name: str) -> int:
    actuator_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
    if actuator_id < 0:
        raise KeyError(f"Missing actuator: {name}")
    return actuator_id


def name_to_joint_qpos_index(model: mujoco.MjModel, name: str) -> int:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    if joint_id < 0:
        raise KeyError(f"Missing joint: {name}")
    return int(model.jnt_qposadr[joint_id])


def set_ctrl(model: mujoco.MjModel, data: mujoco.MjData, alpha: float) -> None:
    data.ctrl[:] = 0.0
    for name, target in ACTUATOR_TARGETS.items():
        data.ctrl[name_to_actuator_id(model, name)] = alpha * target


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


def save_png(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)

    save_png(OUTPUT_DIR / "actuator_demo_start.png", render(model, data))

    duration = 4.0
    dt = float(model.opt.timestep)
    steps = int(duration / dt)
    samples = []
    frames = []

    for step in range(steps):
        alpha = min(1.0, data.time / 2.0)
        set_ctrl(model, data, alpha)
        mujoco.mj_step(model, data)

        if step % 100 == 0:
            sample = {"time": float(data.time)}
            for task_name, (joint_name, _) in TASKS.items():
                sample[joint_name] = float(data.qpos[name_to_joint_qpos_index(model, joint_name)])
            samples.append(sample)

        if step % 80 == 0:
            frames.append(Image.fromarray(render(model, data)))

    save_png(OUTPUT_DIR / "actuator_demo_final.png", render(model, data))
    if frames:
        gif_path = OUTPUT_DIR / "actuator_demo_motion.gif"
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=83, loop=0)
    else:
        gif_path = None

    final_qpos = {
        joint_name: float(data.qpos[name_to_joint_qpos_index(model, joint_name)])
        for joint_name, _ in TASKS.values()
    }
    task_results = {}
    for task_name, (joint_name, threshold) in TASKS.items():
        value = final_qpos[joint_name]
        task_results[task_name] = {
            "joint": joint_name,
            "value": value,
            "threshold": threshold,
            "passed": bool(value >= threshold),
        }

    all_finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
    all_passed = bool(all(item["passed"] for item in task_results.values()) and all_finite)
    summary = {
        "scene_xml": str(SCENE_XML),
        "duration": duration,
        "timestep": dt,
        "steps": steps,
        "actuator_count": int(model.nu),
        "joint_count": int(model.njnt),
        "all_finite": all_finite,
        "contact_count_final": int(data.ncon),
        "task_results": task_results,
        "samples": samples,
        "outputs": {
            "start_png": str(OUTPUT_DIR / "actuator_demo_start.png"),
            "final_png": str(OUTPUT_DIR / "actuator_demo_final.png"),
            "motion_gif": str(gif_path) if gif_path else None,
        },
        "passed": all_passed,
        "status": "PASS" if all_passed else "FAIL",
        "note": "Actuator-driven joint demo using data.ctrl and mj_step; no robot yet.",
    }
    (OUTPUT_DIR / "actuator_demo_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
