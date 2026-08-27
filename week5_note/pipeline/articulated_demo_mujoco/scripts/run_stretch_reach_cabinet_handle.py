#!/usr/bin/env python3
"""Pre-manipulation task: move Stretch gripper near the cabinet handle."""

from __future__ import annotations

import json
import math
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


os.environ.setdefault("MUJOCO_GL", "egl")

ROOT = Path(__file__).resolve().parents[1]
BASE_XML = ROOT / "xml" / "articulated_demo_with_stretch.xml"
TASK_XML = ROOT / "xml" / "articulated_demo_stretch_reach_cabinet_handle.xml"
OUTPUT_DIR = ROOT / "outputs"

BASE_XY = np.array([4.15, 2.92])
BASE_YAW = math.pi / 2.0
RIGHT_HANDLE_GEOM = "010_double_door_cabinet_right_door_right_handle"
TARGET_LIFT = 0.095
TARGET_ARM_EXTEND = 0.52
TARGET_GRIP = 0.035
SUCCESS_DISTANCE = 0.08


def ensure_task_xml() -> None:
    tree = ET.parse(BASE_XML)
    root = tree.getroot()
    root.set("model", "articulated_demo_stretch_reach_cabinet_handle")
    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("Missing worldbody")

    for name in ["cabinet_handle_target_marker", "cabinet_handle_reach_base_marker"]:
        old = worldbody.find(f"./geom[@name='{name}']")
        if old is not None:
            worldbody.remove(old)

    ET.SubElement(
        worldbody,
        "geom",
        {
            "name": "cabinet_handle_target_marker",
            "type": "sphere",
            "pos": "4.882 2.872 0.700",
            "size": "0.045",
            "rgba": "0.1 1 0.25 0.85",
            "contype": "0",
            "conaffinity": "0",
        },
    )
    ET.SubElement(
        worldbody,
        "geom",
        {
            "name": "cabinet_handle_reach_base_marker",
            "type": "cylinder",
            "pos": f"{BASE_XY[0]:.3f} {BASE_XY[1]:.3f} 0.025",
            "size": "0.14 0.018",
            "rgba": "0.2 0.55 1 0.65",
            "contype": "0",
            "conaffinity": "0",
        },
    )
    tree.write(TASK_XML, encoding="utf-8", xml_declaration=True)


def obj_id(model: mujoco.MjModel, obj_type: mujoco.mjtObj, name: str) -> int:
    idx = mujoco.mj_name2id(model, obj_type, name)
    if idx < 0:
        raise KeyError(name)
    return idx


def base_free_qpos_address(model: mujoco.MjModel) -> int:
    base_body = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    for joint_id in range(model.njnt):
        if int(model.jnt_type[joint_id]) == 0 and int(model.jnt_bodyid[joint_id]) == base_body:
            return int(model.jnt_qposadr[joint_id])
    raise RuntimeError("Could not find Stretch base freejoint")


def set_base_pose(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    qadr = base_free_qpos_address(model)
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.qpos[qadr : qadr + 3] = [float(BASE_XY[0]), float(BASE_XY[1]), 0.0]
    data.qpos[qadr + 3 : qadr + 7] = [
        math.cos(BASE_YAW / 2.0),
        0.0,
        0.0,
        math.sin(BASE_YAW / 2.0),
    ]
    mujoco.mj_forward(model, data)


def render(model: mujoco.MjModel, data: mujoco.MjData, view: str) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if view == "top":
        camera.lookat[:] = [4.25, 2.95, 0.65]
        camera.distance = 2.1
        camera.azimuth = 0.0
        camera.elevation = -88.0
    else:
        camera.lookat[:] = [4.55, 2.90, 0.78]
        camera.distance = 1.65
        camera.azimuth = -55.0
        camera.elevation = -28.0
    with mujoco.Renderer(model, width=1000, height=760) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def save(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def joint_qpos(model: mujoco.MjModel, data: mujoco.MjData, joint_name: str) -> float:
    joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    return float(data.qpos[int(model.jnt_qposadr[joint_id])])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_task_xml()

    model = mujoco.MjModel.from_xml_path(str(TASK_XML))
    data = mujoco.MjData(model)
    set_base_pose(model, data)

    lift_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "lift")
    arm_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "arm_extend")
    wrist_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "wrist_yaw")
    grip_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "grip")
    head_pan_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pan")
    head_tilt_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_tilt")

    handle_id = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, RIGHT_HANDLE_GEOM)
    gripper_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "link_gripper_slider")

    save(OUTPUT_DIR / "reach_cabinet_handle_start_top.png", render(model, data, "top"))
    save(OUTPUT_DIR / "reach_cabinet_handle_start_diag.png", render(model, data, "diag"))

    frames: list[Image.Image] = []
    for step in range(3000):
        data.ctrl[:] = 0.0
        data.ctrl[lift_id] = TARGET_LIFT
        data.ctrl[arm_id] = TARGET_ARM_EXTEND
        data.ctrl[wrist_id] = 0.0
        data.ctrl[grip_id] = TARGET_GRIP
        data.ctrl[head_pan_id] = 0.0
        data.ctrl[head_tilt_id] = -0.55
        mujoco.mj_step(model, data)
        if step % 180 == 0:
            frames.append(Image.fromarray(render(model, data, "diag")))

    if not frames:
        frames.append(Image.fromarray(render(model, data, "diag")))

    handle_pos = data.geom_xpos[handle_id].copy()
    gripper_pos = data.xpos[gripper_id].copy()
    distance = float(np.linalg.norm(gripper_pos - handle_pos))
    arm_total = sum(
        joint_qpos(model, data, name)
        for name in ["joint_arm_l0", "joint_arm_l1", "joint_arm_l2", "joint_arm_l3"]
    )
    lift_qpos = joint_qpos(model, data, "joint_lift")

    passed = bool(
        distance <= SUCCESS_DISTANCE
        and arm_total >= 0.45
        and abs(lift_qpos - TARGET_LIFT) <= 0.04
        and np.isfinite(data.qpos).all()
    )

    save(OUTPUT_DIR / "reach_cabinet_handle_final_top.png", render(model, data, "top"))
    save(OUTPUT_DIR / "reach_cabinet_handle_final_diag.png", render(model, data, "diag"))
    gif_path = OUTPUT_DIR / "reach_cabinet_handle_motion.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=83, loop=0)

    summary = {
        "scene_xml": str(TASK_XML),
        "task_name": "stretch_reach_cabinet_handle",
        "base_xy": [float(v) for v in BASE_XY],
        "base_yaw_rad": BASE_YAW,
        "target_handle_geom": RIGHT_HANDLE_GEOM,
        "target_lift": TARGET_LIFT,
        "target_arm_extend": TARGET_ARM_EXTEND,
        "target_grip": TARGET_GRIP,
        "handle_position": [float(v) for v in handle_pos],
        "gripper_position": [float(v) for v in gripper_pos],
        "gripper_to_handle_distance": distance,
        "success_distance": SUCCESS_DISTANCE,
        "lift_qpos": lift_qpos,
        "arm_extension_total": float(arm_total),
        "all_finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "contact_count_final": int(data.ncon),
        "passed": passed,
        "outputs": {
            "start_top": str(OUTPUT_DIR / "reach_cabinet_handle_start_top.png"),
            "start_diag": str(OUTPUT_DIR / "reach_cabinet_handle_start_diag.png"),
            "final_top": str(OUTPUT_DIR / "reach_cabinet_handle_final_top.png"),
            "final_diag": str(OUTPUT_DIR / "reach_cabinet_handle_final_diag.png"),
            "motion_gif": str(gif_path),
        },
        "note": "Pre-manipulation reach test only. It does not grasp or open the cabinet door yet.",
    }
    (OUTPUT_DIR / "reach_cabinet_handle_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
