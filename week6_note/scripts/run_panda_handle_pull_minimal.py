#!/usr/bin/env python3
"""Minimal credible cabinet-handle pull primitive.

This script intentionally stops at a partial door opening. It does not place an
apple, does not close the door, and does not continue to 90 degrees. The goal is
to make one small interaction visually trustworthy before composing longer
tasks.
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from week6_note.scripts import run_panda_reach_cabinet_handle as cab

IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"
TASK_XML = ROOT / "xml" / "articulated_demo_room_with_panda_minimal_handle_pull.xml"
HANDLE_SLEEVE_GEOM = "minimal_visible_right_handle_sleeve"
HANDLE_SUPPORT_GEOMS = (
    "minimal_visible_right_handle_support_upper",
    "minimal_visible_right_handle_support_lower",
    "minimal_visible_right_handle_mount_upper",
    "minimal_visible_right_handle_mount_lower",
)
TARGET_PULL_ANGLE = 0.57
VISIBLE_HANDLE_REACH_BASE = np.array([4.381503, 2.610503, 0.068937])
VISIBLE_HANDLE_REACH_Q = np.array([2.864001, -0.130404, 2.271833, -1.090549, 0.093464, 1.208923, -1.822750])
VISIBLE_HANDLE_PULL_BASE = np.array([4.181900, 2.504100, 0.059100])
VISIBLE_HANDLE_PULL_Q = np.array([2.770500, -0.197700, 2.240400, -0.991400, 0.255400, 1.018500, -1.872600])

GIF_PATH = VIDEO_DIR / "panda_handle_pull_minimal.gif"
SUMMARY_PATH = RESULT_DIR / "panda_handle_pull_minimal_summary.json"


def obj_id(model: mujoco.MjModel, obj_type: mujoco.mjtObj, name: str) -> int:
    idx = mujoco.mj_name2id(model, obj_type, name)
    if idx < 0:
        raise KeyError(name)
    return idx


def ensure_minimal_task_xml() -> None:
    """Create a demo-specific XML with a visible handle that matches the grip."""
    cab.ensure_task_xml()
    tree = ET.parse(cab.TASK_XML)
    root = tree.getroot()
    root.set("model", "articulated_demo_room_with_panda_minimal_handle_pull")

    right_door_body = root.find(".//body[@name='cabinet_right_door']")
    if right_door_body is None:
        raise RuntimeError("Room XML missing cabinet_right_door body")

    for geom in list(right_door_body.findall("geom")):
        if geom.get("name") in {
            cab.RIGHT_HANDLE_GEOM,
            cab.RIGHT_HANDLE_GRASP_PROXY_GEOM,
            HANDLE_SLEEVE_GEOM,
            *HANDLE_SUPPORT_GEOMS,
        }:
            right_door_body.remove(geom)

    ET.SubElement(
        right_door_body,
        "geom",
        {
            "name": HANDLE_SLEEVE_GEOM,
            "type": "box",
            "pos": "-0.113 0.418 0.600",
            "size": "0.024 0.022 0.135",
            "rgba": "0.88 0.86 0.76 1",
            "contype": "2",
            "conaffinity": "3",
        },
    )
    for name, z_pos in [
        ("minimal_visible_right_handle_support_upper", 0.695),
        ("minimal_visible_right_handle_support_lower", 0.505),
    ]:
        ET.SubElement(
            right_door_body,
            "geom",
            {
                "name": name,
                "type": "box",
                "pos": "-0.066 0.418 " + f"{z_pos:.3f}",
                "size": "0.050 0.011 0.012",
                "rgba": "0.82 0.80 0.72 1",
                "contype": "0",
                "conaffinity": "0",
            },
        )
    for name, z_pos in [
        ("minimal_visible_right_handle_mount_upper", 0.695),
        ("minimal_visible_right_handle_mount_lower", 0.505),
    ]:
        ET.SubElement(
            right_door_body,
            "geom",
            {
                "name": name,
                "type": "box",
                "pos": "-0.020 0.418 " + f"{z_pos:.3f}",
                "size": "0.006 0.032 0.026",
                "rgba": "0.76 0.74 0.66 1",
                "contype": "0",
                "conaffinity": "0",
            },
        )

    TASK_XML.parent.mkdir(parents=True, exist_ok=True)
    tree.write(TASK_XML, encoding="utf-8", xml_declaration=True)


def smooth(alpha: float) -> float:
    return alpha * alpha * (3.0 - 2.0 * alpha)


def render(model: mujoco.MjModel, data: mujoco.MjData, view: str) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if view == "top":
        camera.lookat[:] = [4.58, 2.78, 0.68]
        camera.distance = 1.45
        camera.azimuth = 0.0
        camera.elevation = -87.5
    else:
        camera.lookat[:] = [4.70, 2.80, 0.76]
        camera.distance = 1.25
        camera.azimuth = -54.0
        camera.elevation = -26.0
    with mujoco.Renderer(model, width=820, height=620) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def save_image(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def gripper_center(model: mujoco.MjModel, data: mujoco.MjData) -> np.ndarray:
    left_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")
    right_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")
    return (data.xpos[left_id] + data.xpos[right_id]) / 2.0


def geom_pos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray:
    geom_id = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
    return data.geom_xpos[geom_id].copy()


def forbidden_door_slab_penetration(model: mujoco.MjModel, data: mujoco.MjData) -> tuple[int, float | None]:
    door_slab = obj_id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        "009_double_door_cabinet_right_door_right_door_slab",
    )
    panda_body_prefixes = ("link", "hand", "left_finger", "right_finger", "mobile_panda")
    count = 0
    min_dist: float | None = None
    for contact_index in range(data.ncon):
        contact = data.contact[contact_index]
        geom1 = int(contact.geom1)
        geom2 = int(contact.geom2)
        if door_slab not in {geom1, geom2}:
            continue
        other_geom = geom2 if geom1 == door_slab else geom1
        body_id = int(model.geom_bodyid[other_geom])
        body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id) or ""
        if body_name.startswith(panda_body_prefixes):
            count += 1
            dist = float(contact.dist)
            min_dist = dist if min_dist is None else min(min_dist, dist)
    return count, min_dist


def append_qpos_segment(
    *,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    frames: list[Image.Image],
    start_base: np.ndarray,
    end_base: np.ndarray,
    start_q: np.ndarray,
    end_q: np.ndarray,
    start_finger: float,
    end_finger: float,
    start_hinge: float,
    end_hinge: float,
    steps: int,
    frame_stride: int = 7,
) -> None:
    for step, raw_alpha in enumerate(np.linspace(0.0, 1.0, steps)):
        alpha = smooth(float(raw_alpha))
        base = (1.0 - alpha) * start_base + alpha * end_base
        qpos = (1.0 - alpha) * start_q + alpha * end_q
        finger = (1.0 - alpha) * start_finger + alpha * end_finger
        hinge = (1.0 - alpha) * start_hinge + alpha * end_hinge
        cab.set_scene_qpos(model, data, base, qpos, finger, right_hinge_angle=hinge)
        if step % frame_stride == 0:
            frames.append(Image.fromarray(render(model, data, "diag")))


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    ensure_minimal_task_xml()
    model = mujoco.MjModel.from_xml_path(str(TASK_XML))
    data = mujoco.MjData(model)
    frames: list[Image.Image] = []

    cab.set_scene_qpos(model, data, cab.MOBILE_BASE_START, cab.PANDA_HOME, cab.FINGER_OPEN_START, 0.0)
    save_image(IMAGE_DIR / "panda_handle_pull_minimal_start_diag.png", render(model, data, "diag"))
    frames.append(Image.fromarray(render(model, data, "diag")))

    append_qpos_segment(
        model=model,
        data=data,
        frames=frames,
        start_base=cab.MOBILE_BASE_START,
        end_base=VISIBLE_HANDLE_REACH_BASE,
        start_q=cab.PANDA_HOME,
        end_q=cab.PANDA_HOME,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=cab.FINGER_OPEN_START,
        start_hinge=0.0,
        end_hinge=0.0,
        steps=70,
    )

    arm_current = cab.PANDA_HOME.copy()
    for joint_offset in cab.ARM_STAGE_ORDER:
        next_q = arm_current.copy()
        next_q[joint_offset] = VISIBLE_HANDLE_REACH_Q[joint_offset]
        append_qpos_segment(
            model=model,
            data=data,
            frames=frames,
            start_base=VISIBLE_HANDLE_REACH_BASE,
            end_base=VISIBLE_HANDLE_REACH_BASE,
            start_q=arm_current,
            end_q=next_q,
            start_finger=cab.FINGER_OPEN_START,
            end_finger=cab.FINGER_OPEN_START,
            start_hinge=0.0,
            end_hinge=0.0,
            steps=22,
            frame_stride=11,
        )
        arm_current = next_q

    cab.set_scene_qpos(model, data, VISIBLE_HANDLE_REACH_BASE, VISIBLE_HANDLE_REACH_Q, cab.FINGER_OPEN_START, 0.0)
    save_image(IMAGE_DIR / "panda_handle_pull_minimal_reach_diag.png", render(model, data, "diag"))

    append_qpos_segment(
        model=model,
        data=data,
        frames=frames,
        start_base=VISIBLE_HANDLE_REACH_BASE,
        end_base=VISIBLE_HANDLE_REACH_BASE,
        start_q=VISIBLE_HANDLE_REACH_Q,
        end_q=VISIBLE_HANDLE_REACH_Q,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=cab.FINGER_OPEN_FINAL,
        start_hinge=0.0,
        end_hinge=0.0,
        steps=42,
        frame_stride=6,
    )

    cab.set_scene_qpos(model, data, VISIBLE_HANDLE_REACH_BASE, VISIBLE_HANDLE_REACH_Q, cab.FINGER_OPEN_FINAL, 0.0)
    save_image(IMAGE_DIR / "panda_handle_pull_minimal_grasp_diag.png", render(model, data, "diag"))

    append_qpos_segment(
        model=model,
        data=data,
        frames=frames,
        start_base=VISIBLE_HANDLE_REACH_BASE,
        end_base=VISIBLE_HANDLE_PULL_BASE,
        start_q=VISIBLE_HANDLE_REACH_Q,
        end_q=VISIBLE_HANDLE_PULL_Q,
        start_finger=cab.FINGER_OPEN_FINAL,
        end_finger=cab.FINGER_OPEN_FINAL,
        start_hinge=0.0,
        end_hinge=TARGET_PULL_ANGLE,
        steps=85,
        frame_stride=5,
    )

    cab.set_scene_qpos(
        model,
        data,
        VISIBLE_HANDLE_PULL_BASE,
        VISIBLE_HANDLE_PULL_Q,
        cab.FINGER_OPEN_FINAL,
        TARGET_PULL_ANGLE,
    )
    save_image(IMAGE_DIR / "panda_handle_pull_minimal_final_diag.png", render(model, data, "diag"))
    save_image(IMAGE_DIR / "panda_handle_pull_minimal_final_top.png", render(model, data, "top"))
    frames.append(Image.fromarray(render(model, data, "diag")))
    frames[0].save(GIF_PATH, save_all=True, append_images=frames[1:], duration=105, loop=0)

    hinge_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, cab.RIGHT_HINGE_JOINT)
    handle_pos = geom_pos(model, data, HANDLE_SLEEVE_GEOM)
    grip_pos = gripper_center(model, data)
    left_pos = data.xpos[obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")].copy()
    right_pos = data.xpos[obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")].copy()
    forbidden_count, forbidden_min_dist = forbidden_door_slab_penetration(model, data)
    handle_contacts = cab.handle_contact_stats(
        model,
        data,
        obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, HANDLE_SLEEVE_GEOM),
    )

    gripper_to_handle = float(np.linalg.norm(grip_pos - handle_pos))
    finger_span = float(np.linalg.norm(left_pos - right_pos))
    final_hinge = float(data.qpos[int(model.jnt_qposadr[hinge_id])])
    passed = bool(
        abs(final_hinge - TARGET_PULL_ANGLE) <= 0.01
        and gripper_to_handle <= 0.035
        and int(handle_contacts["unique_finger_count"]) >= 2
        and forbidden_count == 0
    )

    summary = {
        "task_name": "panda_minimal_handle_pull",
        "scope": "single credible primitive: reach, grasp visible handle, pull door to 0.57 rad, stop",
        "scene_xml": str(TASK_XML),
        "motion_gif": str(GIF_PATH),
        "final_right_hinge_angle": final_hinge,
        "target_right_hinge_angle": TARGET_PULL_ANGLE,
        "gripper_position": [float(v) for v in grip_pos],
        "handle_position": [float(v) for v in handle_pos],
        "gripper_to_handle_distance": gripper_to_handle,
        "visible_handle_geom": HANDLE_SLEEVE_GEOM,
        "finger_span": finger_span,
        "handle_unique_finger_contacts": int(handle_contacts["unique_finger_count"]),
        "handle_finger_bodies": handle_contacts["finger_bodies"],
        "forbidden_door_slab_contact_count": forbidden_count,
        "forbidden_door_slab_min_dist": forbidden_min_dist,
        "passed": passed,
        "limitations": [
            "door hinge and arm are still driven by scripted qpos waypoints",
            "this intentionally stops at a partial opening instead of attempting a full 90-degree task",
            "no apple placement is included in this primitive",
        ],
        "outputs": {
            "start_diag": str(IMAGE_DIR / "panda_handle_pull_minimal_start_diag.png"),
            "reach_diag": str(IMAGE_DIR / "panda_handle_pull_minimal_reach_diag.png"),
            "grasp_diag": str(IMAGE_DIR / "panda_handle_pull_minimal_grasp_diag.png"),
            "final_diag": str(IMAGE_DIR / "panda_handle_pull_minimal_final_diag.png"),
            "final_top": str(IMAGE_DIR / "panda_handle_pull_minimal_final_top.png"),
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
