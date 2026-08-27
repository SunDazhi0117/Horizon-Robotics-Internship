#!/usr/bin/env python3
"""Combined task: navigate Stretch to the cabinet and reach its handle."""

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
TASK_XML = ROOT / "xml" / "articulated_demo_stretch_navigate_and_reach_cabinet.xml"
OUTPUT_DIR = ROOT / "outputs"

START_XY = np.array([3.10, 2.35])
START_YAW = math.pi
WAYPOINTS = [
    np.array([3.55, 2.35]),
    np.array([3.55, 2.95]),
    np.array([4.22, 2.86]),
]
REACH_BASE_XY = WAYPOINTS[-1]
REACH_BASE_YAW = math.pi / 2.0
WAYPOINT_RADIUS = 0.22
NAV_SUCCESS_RADIUS = 0.045
YAW_SUCCESS_RAD = 0.055

RIGHT_HANDLE_GEOM = "010_double_door_cabinet_right_door_right_handle"
TARGET_LIFT = 0.095
TARGET_ARM_EXTEND = 0.52
TARGET_GRIP = 0.035
REACH_SUCCESS_DISTANCE = 0.08


def ensure_task_xml() -> None:
    tree = ET.parse(BASE_XML)
    root = tree.getroot()
    root.set("model", "articulated_demo_stretch_navigate_and_reach_cabinet")
    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("Missing worldbody")

    marker_names = [
        "combined_waypoint_0",
        "combined_waypoint_1",
        "combined_reach_base_marker",
        "combined_cabinet_handle_target_marker",
    ]
    for name in marker_names:
        old = worldbody.find(f"./geom[@name='{name}']")
        if old is not None:
            worldbody.remove(old)

    specs = [
        ("combined_waypoint_0", WAYPOINTS[0], "0.2 0.55 1 0.65"),
        ("combined_waypoint_1", WAYPOINTS[1], "0.2 0.55 1 0.65"),
        ("combined_reach_base_marker", REACH_BASE_XY, "1 0.85 0.1 0.75"),
    ]
    for name, xy, rgba in specs:
        ET.SubElement(
            worldbody,
            "geom",
            {
                "name": name,
                "type": "cylinder",
                "pos": f"{xy[0]:.3f} {xy[1]:.3f} 0.025",
                "size": "0.14 0.018",
                "rgba": rgba,
                "contype": "0",
                "conaffinity": "0",
            },
        )

    ET.SubElement(
        worldbody,
        "geom",
        {
            "name": "combined_cabinet_handle_target_marker",
            "type": "sphere",
            "pos": "4.882 2.872 0.700",
            "size": "0.045",
            "rgba": "0.1 1 0.25 0.85",
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


def set_base_pose(model: mujoco.MjModel, data: mujoco.MjData, xy: np.ndarray, yaw: float) -> None:
    qadr = base_free_qpos_address(model)
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.qpos[qadr : qadr + 3] = [float(xy[0]), float(xy[1]), 0.0]
    data.qpos[qadr + 3 : qadr + 7] = [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]
    mujoco.mj_forward(model, data)


def get_yaw(model: mujoco.MjModel, data: mujoco.MjData) -> float:
    qadr = base_free_qpos_address(model)
    quat = data.qpos[qadr + 3 : qadr + 7]
    w, _, _, z = quat
    return math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z)


def wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def joint_qpos(model: mujoco.MjModel, data: mujoco.MjData, joint_name: str) -> float:
    joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    return float(data.qpos[int(model.jnt_qposadr[joint_id])])


def render(model: mujoco.MjModel, data: mujoco.MjData, view: str) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if view == "top":
        camera.lookat[:] = [3.85, 2.75, 0.45]
        camera.distance = 3.1
        camera.azimuth = 0.0
        camera.elevation = -88.0
    else:
        camera.lookat[:] = [4.45, 2.92, 0.78]
        camera.distance = 2.0
        camera.azimuth = -55.0
        camera.elevation = -30.0
    with mujoco.Renderer(model, width=1000, height=760) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def save(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_task_xml()

    model = mujoco.MjModel.from_xml_path(str(TASK_XML))
    data = mujoco.MjData(model)
    set_base_pose(model, data, START_XY, START_YAW)

    base_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    forward_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "forward")
    turn_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "turn")
    lift_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "lift")
    arm_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "arm_extend")
    wrist_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "wrist_yaw")
    grip_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "grip")
    head_pan_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pan")
    head_tilt_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_tilt")
    handle_id = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, RIGHT_HANDLE_GEOM)
    gripper_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "link_gripper_slider")

    save(OUTPUT_DIR / "combined_nav_reach_start_top.png", render(model, data, "top"))

    frames: list[Image.Image] = []
    reached_waypoints = []
    path = []
    waypoint_index = 0
    nav_max_time = 24.0

    while data.time < nav_max_time and waypoint_index < len(WAYPOINTS):
        pos = data.xpos[base_id][:2].copy()
        target = WAYPOINTS[waypoint_index]
        vector = target - pos
        distance = float(np.linalg.norm(vector))
        path.append(
            {
                "time": float(data.time),
                "phase": "navigate",
                "x": float(pos[0]),
                "y": float(pos[1]),
                "waypoint_index": waypoint_index,
                "distance": distance,
            }
        )
        if len(path) % 280 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

        radius = NAV_SUCCESS_RADIUS if waypoint_index == len(WAYPOINTS) - 1 else WAYPOINT_RADIUS
        if distance <= radius:
            reached_waypoints.append(
                {
                    "waypoint_index": waypoint_index,
                    "time": float(data.time),
                    "x": float(pos[0]),
                    "y": float(pos[1]),
                    "distance": distance,
                }
            )
            waypoint_index += 1
            continue

        desired_yaw = math.atan2(vector[1], vector[0]) + math.pi
        yaw_error = wrap_angle(desired_yaw - get_yaw(model, data))
        turn_ctrl = float(np.clip(-0.8 * yaw_error, -0.6, 0.6))
        forward_ctrl = 0.48 if abs(yaw_error) < 0.55 else 0.16

        data.ctrl[:] = 0.0
        data.ctrl[forward_id] = forward_ctrl
        data.ctrl[turn_id] = turn_ctrl
        data.ctrl[lift_id] = 0.18
        data.ctrl[arm_id] = 0.06
        data.ctrl[head_pan_id] = 0.2
        mujoco.mj_step(model, data)

    nav_final_pos = data.xpos[base_id][:2].copy()
    nav_distance = float(np.linalg.norm(nav_final_pos - REACH_BASE_XY))
    nav_passed = bool(
        waypoint_index >= len(WAYPOINTS)
        and nav_distance <= NAV_SUCCESS_RADIUS
        and np.isfinite(data.qpos).all()
    )

    alignment_steps = 0
    for alignment_steps in range(6000):
        yaw_error = wrap_angle(REACH_BASE_YAW - get_yaw(model, data))
        if abs(yaw_error) <= YAW_SUCCESS_RAD:
            break
        data.ctrl[:] = 0.0
        data.ctrl[turn_id] = float(np.clip(-0.8 * yaw_error, -0.45, 0.45))
        data.ctrl[lift_id] = 0.10
        data.ctrl[arm_id] = 0.08
        data.ctrl[head_pan_id] = 0.0
        mujoco.mj_step(model, data)
        if alignment_steps % 90 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

    aligned_yaw_error = wrap_angle(REACH_BASE_YAW - get_yaw(model, data))
    alignment_passed = bool(abs(aligned_yaw_error) <= YAW_SUCCESS_RAD)
    save(OUTPUT_DIR / "combined_nav_reach_after_navigation_top.png", render(model, data, "top"))

    reach_start_time = float(data.time)
    for step in range(3000):
        data.ctrl[:] = 0.0
        data.ctrl[lift_id] = TARGET_LIFT
        data.ctrl[arm_id] = TARGET_ARM_EXTEND
        data.ctrl[wrist_id] = 0.0
        data.ctrl[grip_id] = TARGET_GRIP
        data.ctrl[head_pan_id] = 0.0
        data.ctrl[head_tilt_id] = -0.55
        mujoco.mj_step(model, data)
        if step % 75 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

    if not frames:
        frames.append(Image.fromarray(render(model, data, "top")))

    handle_pos = data.geom_xpos[handle_id].copy()
    gripper_pos = data.xpos[gripper_id].copy()
    reach_distance = float(np.linalg.norm(gripper_pos - handle_pos))
    arm_total = sum(
        joint_qpos(model, data, name)
        for name in ["joint_arm_l0", "joint_arm_l1", "joint_arm_l2", "joint_arm_l3"]
    )
    lift_qpos = joint_qpos(model, data, "joint_lift")
    reach_passed = bool(
        reach_distance <= REACH_SUCCESS_DISTANCE
        and arm_total >= 0.45
        and abs(lift_qpos - TARGET_LIFT) <= 0.04
        and np.isfinite(data.qpos).all()
    )
    passed = bool(nav_passed and reach_passed)

    save(OUTPUT_DIR / "combined_nav_reach_final_top.png", render(model, data, "top"))
    save(OUTPUT_DIR / "combined_nav_reach_final_diag.png", render(model, data, "diag"))
    gif_path = OUTPUT_DIR / "combined_nav_reach_motion.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=105, loop=0)

    summary = {
        "scene_xml": str(TASK_XML),
        "task_name": "stretch_navigate_and_reach_cabinet_handle",
        "start_xy": [float(v) for v in START_XY],
        "start_yaw_rad": START_YAW,
        "waypoints": [[float(v) for v in xy] for xy in WAYPOINTS],
        "reached_waypoints": reached_waypoints,
        "nav_success_radius": NAV_SUCCESS_RADIUS,
        "nav_final_xy": [float(v) for v in nav_final_pos],
        "nav_distance_to_reach_base": nav_distance,
        "nav_passed": nav_passed,
        "reach_base_xy": [float(v) for v in REACH_BASE_XY],
        "reach_base_yaw_rad": REACH_BASE_YAW,
        "base_pose_adjusted_for_reach": False,
        "alignment_steps": int(alignment_steps),
        "aligned_yaw_error": float(aligned_yaw_error),
        "yaw_success_rad": YAW_SUCCESS_RAD,
        "alignment_passed": alignment_passed,
        "target_handle_geom": RIGHT_HANDLE_GEOM,
        "handle_position": [float(v) for v in handle_pos],
        "gripper_position": [float(v) for v in gripper_pos],
        "gripper_to_handle_distance": reach_distance,
        "reach_success_distance": REACH_SUCCESS_DISTANCE,
        "lift_qpos": lift_qpos,
        "arm_extension_total": float(arm_total),
        "reach_elapsed_time": float(data.time - reach_start_time),
        "all_finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "contact_count_final": int(data.ncon),
        "reach_passed": reach_passed,
        "passed": bool(passed and alignment_passed),
        "outputs": {
            "start_top": str(OUTPUT_DIR / "combined_nav_reach_start_top.png"),
            "after_navigation_top": str(OUTPUT_DIR / "combined_nav_reach_after_navigation_top.png"),
            "final_top": str(OUTPUT_DIR / "combined_nav_reach_final_top.png"),
            "final_diag": str(OUTPUT_DIR / "combined_nav_reach_final_diag.png"),
            "motion_gif": str(gif_path),
        },
        "note": "Combined navigation + pre-manipulation reach. The base approaches and aligns through MuJoCo controls; this is not full autonomous manipulation yet.",
    }
    (OUTPUT_DIR / "combined_nav_reach_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
