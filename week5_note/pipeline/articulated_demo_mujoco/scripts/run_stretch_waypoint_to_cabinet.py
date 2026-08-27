#!/usr/bin/env python3
"""Waypoint navigation task for Stretch to reach the cabinet front."""

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
TASK_XML = ROOT / "xml" / "articulated_demo_stretch_waypoint_cabinet.xml"
OUTPUT_DIR = ROOT / "outputs"

START_XY = np.array([3.10, 2.35])
START_YAW = math.pi
WAYPOINTS = [
    np.array([3.55, 2.35]),
    np.array([3.55, 2.95]),
    np.array([4.45, 2.95]),
]
SUCCESS_RADIUS = 0.35
WAYPOINT_RADIUS = 0.22


def ensure_task_xml() -> None:
    tree = ET.parse(BASE_XML)
    root = tree.getroot()
    root.set("model", "articulated_demo_stretch_waypoint_cabinet")
    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("Missing worldbody")

    for name in ["cabinet_goal_marker", "cabinet_waypoint_0", "cabinet_waypoint_1"]:
        old = worldbody.find(f"./geom[@name='{name}']")
        if old is not None:
            worldbody.remove(old)

    marker_specs = [
        ("cabinet_waypoint_0", WAYPOINTS[0], "0.2 0.55 1 0.75"),
        ("cabinet_waypoint_1", WAYPOINTS[1], "0.2 0.55 1 0.75"),
        ("cabinet_goal_marker", WAYPOINTS[2], "0.1 1 0.25 0.85"),
    ]
    for name, xy, rgba in marker_specs:
        ET.SubElement(
            worldbody,
            "geom",
            {
                "name": name,
                "type": "cylinder",
                "pos": f"{xy[0]:.3f} {xy[1]:.3f} 0.025",
                "size": "0.16 0.018",
                "rgba": rgba,
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


def render(model: mujoco.MjModel, data: mujoco.MjData, view: str) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if view == "top":
        camera.lookat[:] = [3.75, 2.65, 0.35]
        camera.distance = 3.2
        camera.azimuth = 0.0
        camera.elevation = -88.0
    else:
        camera.lookat[:] = [3.75, 2.65, 0.8]
        camera.distance = 4.2
        camera.azimuth = -35.0
        camera.elevation = -35.0
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
    head_pan_id = obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pan")

    save(OUTPUT_DIR / "waypoint_cabinet_start_top.png", render(model, data, "top"))
    save(OUTPUT_DIR / "waypoint_cabinet_start_diag.png", render(model, data, "diag"))

    path = []
    frames = []
    waypoint_index = 0
    reached_waypoints = []
    max_time = 18.0

    while data.time < max_time and waypoint_index < len(WAYPOINTS):
        pos = data.xpos[base_id][:2].copy()
        target = WAYPOINTS[waypoint_index]
        vector = target - pos
        distance = float(np.linalg.norm(vector))

        path.append(
            {
                "time": float(data.time),
                "x": float(pos[0]),
                "y": float(pos[1]),
                "waypoint_index": waypoint_index,
                "distance": distance,
            }
        )
        if len(path) % 300 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

        radius = SUCCESS_RADIUS if waypoint_index == len(WAYPOINTS) - 1 else WAYPOINT_RADIUS
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
        data.ctrl[lift_id] = 0.20
        data.ctrl[arm_id] = 0.12
        data.ctrl[head_pan_id] = 0.2
        mujoco.mj_step(model, data)

    if not frames:
        frames.append(Image.fromarray(render(model, data, "top")))

    final_pos = data.xpos[base_id][:2].copy()
    final_distance = float(np.linalg.norm(final_pos - WAYPOINTS[-1]))
    passed = bool(
        waypoint_index >= len(WAYPOINTS)
        and final_distance <= SUCCESS_RADIUS
        and np.isfinite(data.qpos).all()
    )

    save(OUTPUT_DIR / "waypoint_cabinet_final_top.png", render(model, data, "top"))
    save(OUTPUT_DIR / "waypoint_cabinet_final_diag.png", render(model, data, "diag"))
    gif_path = OUTPUT_DIR / "waypoint_cabinet_motion.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=83, loop=0)

    summary = {
        "scene_xml": str(TASK_XML),
        "task_name": "stretch_waypoint_navigation_to_cabinet_front",
        "start_xy": [float(x) for x in START_XY],
        "waypoints": [[float(v) for v in xy] for xy in WAYPOINTS],
        "waypoint_radius": WAYPOINT_RADIUS,
        "success_radius": SUCCESS_RADIUS,
        "reached_waypoints": reached_waypoints,
        "final_xy": [float(x) for x in final_pos],
        "final_distance_to_target": final_distance,
        "elapsed_time": float(data.time),
        "path_sample_count": len(path),
        "all_finite": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "contact_count_final": int(data.ncon),
        "passed": passed,
        "outputs": {
            "start_top": str(OUTPUT_DIR / "waypoint_cabinet_start_top.png"),
            "start_diag": str(OUTPUT_DIR / "waypoint_cabinet_start_diag.png"),
            "final_top": str(OUTPUT_DIR / "waypoint_cabinet_final_top.png"),
            "final_diag": str(OUTPUT_DIR / "waypoint_cabinet_final_diag.png"),
            "motion_gif": str(gif_path),
        },
        "note": "Waypoint navigation task with simple heading controller; no manipulation yet.",
    }
    (OUTPUT_DIR / "waypoint_cabinet_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
