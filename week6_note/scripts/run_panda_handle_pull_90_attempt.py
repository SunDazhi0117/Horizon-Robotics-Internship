#!/usr/bin/env python3
"""Attempt a full 90-degree cabinet-handle pull.

This builds on the trusted minimal handle-pull primitive. It keeps the visible
handle replacement from that script, then follows a newly fitted qpos waypoint
track from the accepted 0.57 rad pose to 90 degrees.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from week6_note.scripts import run_panda_handle_pull_minimal as minimal
from week6_note.scripts import run_panda_reach_cabinet_handle as cab

IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

GIF_PATH = VIDEO_DIR / "panda_handle_pull_90_attempt.gif"
SUMMARY_PATH = RESULT_DIR / "panda_handle_pull_90_attempt_summary.json"
FRAME_SHEET_PATH = IMAGE_DIR / "panda_handle_pull_90_attempt_frames_sheet.png"

TARGET_PULL_ANGLE = 1.57079632679
GRASP_FINGER_OPENING = 0.019

# Columns: hinge, base_x, base_y, base_yaw, panda joint1..joint7.
FOLLOW_90_WAYPOINTS = np.array(
    [
        [0.000000, 4.198328, 2.506919, 0.056101, 2.702813, -0.966857, 1.801164, -0.643152, -0.443267, 1.855007, -1.149381],
        [0.098175, 4.175411, 2.494573, 0.057853, 2.743197, -0.969653, 1.775696, -0.661960, -0.461426, 1.772991, -1.143098],
        [0.196350, 4.146140, 2.463913, 0.059253, 2.775449, -0.964987, 1.774512, -0.678675, -0.466771, 1.781746, -1.139263],
        [0.294524, 4.109954, 2.410366, 0.060178, 2.796748, -0.949761, 1.804520, -0.693846, -0.456736, 1.909104, -1.139270],
        [0.392699, 4.075705, 2.356334, 0.060822, 2.811602, -0.932001, 1.836898, -0.715116, -0.446827, 2.049115, -1.144186],
        [0.490874, 4.043670, 2.302867, 0.061177, 2.819783, -0.910647, 1.872780, -0.743785, -0.436739, 2.202652, -1.155960],
        [0.589049, 4.014385, 2.251104, 0.061242, 2.821264, -0.884007, 1.914362, -0.781526, -0.426066, 2.370111, -1.177788],
        [0.687223, 3.988894, 2.202132, 0.061034, 2.816491, -0.849028, 1.966009, -0.830981, -0.414640, 2.550822, -1.214943],
        [0.785398, 3.969305, 2.156580, 0.060618, 2.806891, -0.799497, 2.036393, -0.897260, -0.404156, 2.741863, -1.275508],
        [0.883573, 3.960073, 2.113689, 0.060108, 2.795157, -0.722854, 2.140754, -0.990677, -0.403350, 2.935563, -1.367612],
        [0.981748, 3.969789, 2.070409, 0.059568, 2.782708, -0.601154, 2.293972, -1.127515, -0.434557, 3.117338, -1.483831],
        [1.079922, 4.010925, 2.023626, 0.058900, 2.767301, -0.428202, 2.485440, -1.320014, -0.520989, 3.271955, -1.582209],
        [1.178097, 4.101288, 1.973564, 0.059012, 2.769896, -0.216255, 2.668199, -1.562763, -0.677700, 3.397218, -1.595328],
        [1.276272, 4.243030, 1.934270, 0.062877, 2.858921, 0.002117, 2.755390, -1.790210, -0.956013, 3.507031, -1.433554],
        [1.374447, 4.289915, 1.912770, 0.064260, 2.893062, 0.097039, 2.759350, -1.875996, -1.090997, 3.557713, -1.341365],
        [1.472622, 4.324153, 1.893783, 0.064774, 2.897300, 0.162778, 2.761053, -1.918922, -1.243373, 3.625000, -1.218776],
        [1.570796, 4.358252, 1.876601, 0.116366, 2.897300, 0.226539, 2.721136, -1.959595, -1.360350, 3.689711, -1.137390],
    ],
    dtype=float,
)

HORIZONTAL_GRASP_BASE = FOLLOW_90_WAYPOINTS[0, 1:4]
HORIZONTAL_GRASP_Q = FOLLOW_90_WAYPOINTS[0, 4:11]


def smooth(alpha: float) -> float:
    return alpha * alpha * (3.0 - 2.0 * alpha)


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
    view: str = "diag",
    frame_stride: int = 8,
) -> list[dict[str, float]]:
    samples: list[dict[str, float]] = []
    for step, raw_alpha in enumerate(np.linspace(0.0, 1.0, steps)):
        alpha = smooth(float(raw_alpha))
        base = (1.0 - alpha) * start_base + alpha * end_base
        qpos = (1.0 - alpha) * start_q + alpha * end_q
        finger = (1.0 - alpha) * start_finger + alpha * end_finger
        hinge = (1.0 - alpha) * start_hinge + alpha * end_hinge
        cab.set_scene_qpos(model, data, base, qpos, finger, right_hinge_angle=hinge)
        if step % frame_stride == 0:
            frames.append(Image.fromarray(minimal.render(model, data, view)))
        samples.append(sample_state(model, data, hinge))
    return samples


def sample_state(model: mujoco.MjModel, data: mujoco.MjData, hinge: float) -> dict[str, float]:
    handle_pos = minimal.geom_pos(model, data, minimal.HANDLE_SLEEVE_GEOM)
    grip_pos = minimal.gripper_center(model, data)
    left_pos = data.xpos[minimal.obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")].copy()
    right_pos = data.xpos[minimal.obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")].copy()
    hand_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "hand")
    hand_tool_axis = data.xmat[hand_id].reshape(3, 3)[:, 2].copy()
    finger_delta = right_pos - left_pos
    contacts = cab.handle_contact_stats(
        model,
        data,
        minimal.obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, minimal.HANDLE_SLEEVE_GEOM),
    )
    forbidden_count, forbidden_min_dist = minimal.forbidden_door_slab_penetration(model, data)
    return {
        "hinge": float(hinge),
        "gripper_to_handle_distance": float(np.linalg.norm(grip_pos - handle_pos)),
        "tool_axis_z_abs": float(abs(hand_tool_axis[2])),
        "finger_xy_separation": float(np.linalg.norm(finger_delta[:2])),
        "finger_z_separation": float(abs(finger_delta[2])),
        "handle_unique_finger_contacts": float(contacts["unique_finger_count"]),
        "forbidden_door_slab_contact_count": float(forbidden_count),
        "forbidden_door_slab_min_dist": float(forbidden_min_dist) if forbidden_min_dist is not None else 0.0,
    }


def save_frame_sheet(frames: list[Image.Image]) -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    chosen = frames[:: max(1, len(frames) // 12)][:12]
    thumb_w, thumb_h = 410, 310
    sheet = Image.new("RGB", (thumb_w * 3, thumb_h * 4), (20, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(chosen):
        thumb = frame.resize((thumb_w, thumb_h))
        x = (index % 3) * thumb_w
        y = (index // 3) * thumb_h
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + 96, y + 24), fill=(0, 0, 0))
        draw.text((x + 6, y + 5), f"frame_{index:03d}", fill=(255, 255, 255))
    sheet.save(FRAME_SHEET_PATH)


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    minimal.ensure_minimal_task_xml()

    model = mujoco.MjModel.from_xml_path(str(minimal.TASK_XML))
    data = mujoco.MjData(model)
    frames: list[Image.Image] = []
    validation_samples: list[dict[str, float]] = []

    cab.set_scene_qpos(model, data, cab.MOBILE_BASE_START, cab.PANDA_HOME, cab.FINGER_OPEN_START, 0.0)
    frames.append(Image.fromarray(minimal.render(model, data, "diag")))

    append_qpos_segment(
        model=model,
        data=data,
        frames=frames,
        start_base=cab.MOBILE_BASE_START,
        end_base=HORIZONTAL_GRASP_BASE,
        start_q=cab.PANDA_HOME,
        end_q=cab.PANDA_HOME,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=cab.FINGER_OPEN_START,
        start_hinge=0.0,
        end_hinge=0.0,
        steps=70,
        frame_stride=10,
    )

    arm_current = cab.PANDA_HOME.copy()
    for joint_offset in cab.ARM_STAGE_ORDER:
        next_q = arm_current.copy()
        next_q[joint_offset] = HORIZONTAL_GRASP_Q[joint_offset]
        append_qpos_segment(
            model=model,
            data=data,
            frames=frames,
            start_base=HORIZONTAL_GRASP_BASE,
            end_base=HORIZONTAL_GRASP_BASE,
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

    append_qpos_segment(
        model=model,
        data=data,
        frames=frames,
        start_base=HORIZONTAL_GRASP_BASE,
        end_base=HORIZONTAL_GRASP_BASE,
        start_q=HORIZONTAL_GRASP_Q,
        end_q=HORIZONTAL_GRASP_Q,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=GRASP_FINGER_OPENING,
        start_hinge=0.0,
        end_hinge=0.0,
        steps=42,
        frame_stride=8,
    )

    for waypoint_a, waypoint_b in zip(FOLLOW_90_WAYPOINTS[:-1], FOLLOW_90_WAYPOINTS[1:]):
        validation_samples += append_qpos_segment(
            model=model,
            data=data,
            frames=frames,
            start_base=waypoint_a[1:4],
            end_base=waypoint_b[1:4],
            start_q=waypoint_a[4:11],
            end_q=waypoint_b[4:11],
            start_finger=GRASP_FINGER_OPENING,
            end_finger=GRASP_FINGER_OPENING,
            start_hinge=float(waypoint_a[0]),
            end_hinge=float(waypoint_b[0]),
            steps=24,
            frame_stride=6,
        )

    final = FOLLOW_90_WAYPOINTS[-1]
    cab.set_scene_qpos(
        model,
        data,
        final[1:4],
        final[4:11],
        GRASP_FINGER_OPENING,
        right_hinge_angle=TARGET_PULL_ANGLE,
    )
    Image.fromarray(minimal.render(model, data, "diag")).save(
        IMAGE_DIR / "panda_handle_pull_90_attempt_final_diag.png"
    )
    Image.fromarray(minimal.render(model, data, "top")).save(
        IMAGE_DIR / "panda_handle_pull_90_attempt_final_top.png"
    )
    frames.append(Image.fromarray(minimal.render(model, data, "diag")))
    frames[0].save(GIF_PATH, save_all=True, append_images=frames[1:], duration=95, loop=0)
    save_frame_sheet(frames)

    final_sample = sample_state(model, data, TARGET_PULL_ANGLE)
    max_distance = max(sample["gripper_to_handle_distance"] for sample in validation_samples)
    max_tool_axis_z_abs = max(sample["tool_axis_z_abs"] for sample in validation_samples)
    max_finger_z_separation = max(sample["finger_z_separation"] for sample in validation_samples)
    min_finger_xy_separation = min(sample["finger_xy_separation"] for sample in validation_samples)
    min_unique_contacts = min(sample["handle_unique_finger_contacts"] for sample in validation_samples)
    max_forbidden_contacts = max(sample["forbidden_door_slab_contact_count"] for sample in validation_samples)
    min_forbidden_dist = min(sample["forbidden_door_slab_min_dist"] for sample in validation_samples)
    passed_numeric = bool(
        abs(final_sample["hinge"] - TARGET_PULL_ANGLE) <= 0.01
        and final_sample["gripper_to_handle_distance"] <= 0.035
        and final_sample["handle_unique_finger_contacts"] >= 2
        and max_distance <= 0.04
        and max_tool_axis_z_abs <= 0.01
        and max_finger_z_separation <= 0.01
        and min_finger_xy_separation >= 0.035
        and max_forbidden_contacts == 0
    )
    summary = {
        "task_name": "panda_handle_pull_90_attempt",
        "scope": "reach, grasp visible handle, then follow the moving handle to 90 degrees",
        "target_right_hinge_angle": TARGET_PULL_ANGLE,
        "final_sample": final_sample,
        "max_gripper_to_handle_distance": max_distance,
        "max_tool_axis_z_abs": max_tool_axis_z_abs,
        "max_finger_z_separation": max_finger_z_separation,
        "min_finger_xy_separation": min_finger_xy_separation,
        "grasp_finger_opening": GRASP_FINGER_OPENING,
        "min_handle_unique_finger_contacts": min_unique_contacts,
        "max_forbidden_door_slab_contact_count": max_forbidden_contacts,
        "min_forbidden_door_slab_contact_dist": min_forbidden_dist,
        "passed_numeric": passed_numeric,
        "requires_visual_review": True,
        "motion_gif": str(GIF_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "outputs": {
            "final_diag": str(IMAGE_DIR / "panda_handle_pull_90_attempt_final_diag.png"),
            "final_top": str(IMAGE_DIR / "panda_handle_pull_90_attempt_final_top.png"),
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed_numeric:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
