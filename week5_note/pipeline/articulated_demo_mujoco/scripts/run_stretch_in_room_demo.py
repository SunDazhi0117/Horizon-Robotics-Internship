#!/usr/bin/env python3
"""Drive the real Stretch model inside the articulated demo room."""

from __future__ import annotations

import json
import os
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "xml" / "articulated_demo_with_stretch.xml"
OUTPUT_DIR = ROOT / "outputs"


def obj_id(model: mujoco.MjModel, obj_type: mujoco.mjtObj, name: str) -> int:
    idx = mujoco.mj_name2id(model, obj_type, name)
    if idx < 0:
        raise KeyError(name)
    return idx


def render(model: mujoco.MjModel, data: mujoco.MjData, view: str) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if view == "top":
        camera.lookat[:] = [2.5, 2.25, 0.5]
        camera.distance = 5.4
        camera.azimuth = 0.0
        camera.elevation = -88.0
    else:
        camera.lookat[:] = [2.5, 2.25, 0.8]
        camera.distance = 6.2
        camera.azimuth = -45.0
        camera.elevation = -32.0

    with mujoco.Renderer(model, width=1000, height=760) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def save(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)

    base_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    forward_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "forward")
    turn_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "turn")
    lift_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "lift")
    arm_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "arm_extend")
    head_pan_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pan")

    start_pos = data.xpos[base_id].copy()
    save(OUTPUT_DIR / "stretch_room_start_top.png", render(model, data, "top"))
    save(OUTPUT_DIR / "stretch_room_start_diag.png", render(model, data, "diag"))

    frames = []
    steps = int(4.0 / float(model.opt.timestep))
    for step in range(steps):
        data.ctrl[:] = 0.0
        # Keep room articulated objects still; drive only Stretch.
        data.ctrl[forward_id] = 0.35
        data.ctrl[turn_id] = 0.05
        data.ctrl[lift_id] = 0.20
        data.ctrl[arm_id] = 0.18
        data.ctrl[head_pan_id] = 0.35
        mujoco.mj_step(model, data)
        if step % 80 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

    final_pos = data.xpos[base_id].copy()
    save(OUTPUT_DIR / "stretch_room_final_top.png", render(model, data, "top"))
    save(OUTPUT_DIR / "stretch_room_final_diag.png", render(model, data, "diag"))

    gif_path = OUTPUT_DIR / "stretch_room_motion.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=83, loop=0)

    moved = float(np.linalg.norm(final_pos[:2] - start_pos[:2]))
    summary = {
        "scene_xml": str(SCENE_XML),
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "nq": int(model.nq),
        "nu": int(model.nu),
        "nmesh": int(model.nmesh),
        "start_pos": [float(x) for x in start_pos],
        "final_pos": [float(x) for x in final_pos],
        "moved_distance_xy": moved,
        "all_finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "contact_count_final": int(data.ncon),
        "outputs": {
            "start_top": str(OUTPUT_DIR / "stretch_room_start_top.png"),
            "start_diag": str(OUTPUT_DIR / "stretch_room_start_diag.png"),
            "final_top": str(OUTPUT_DIR / "stretch_room_final_top.png"),
            "final_diag": str(OUTPUT_DIR / "stretch_room_final_diag.png"),
            "motion_gif": str(gif_path),
        },
        "passed": bool(moved > 0.1 and np.isfinite(data.qpos).all()),
        "note": "Real Stretch model in generated articulated room; smoke test only, not manipulation.",
    }
    (OUTPUT_DIR / "stretch_room_demo_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
