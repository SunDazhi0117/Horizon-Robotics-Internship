#!/usr/bin/env python3
"""Level 2: keep the accepted grasp rigidly attached while opening.

An earlier clearance optimization could move the gripper away from the handle.
This task starts from the accepted Level 1 grasp and, for every door angle,
solves the Panda/base pose so the hand keeps the same transform relative to
the moving cabinet door.  The dense solved trajectory is validated and
rendered directly, without interpolating between sparse poses.
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
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from week6_note.scripts import run_panda_handle_pull_90_attempt as open90
from week6_note.scripts import run_panda_handle_pull_minimal as minimal
from week6_note.scripts import run_panda_reach_cabinet_handle as cab
from week7_note.scripts import run_level_1_handle_grasp as level_1

IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

GIF_PATH = VIDEO_DIR / "level_2_handle_follow_open_90.gif"
TOP_GIF_PATH = VIDEO_DIR / "level_2_handle_follow_open_90_top_view.gif"
SUMMARY_PATH = RESULT_DIR / "level_2_handle_follow_open_90_summary.json"
TRAJECTORY_PATH = RESULT_DIR / "level_2_handle_follow_open_90_trajectory.json"
FRAME_SHEET_PATH = IMAGE_DIR / "level_2_handle_follow_open_90_frames_sheet.png"
TOP_FRAME_SHEET_PATH = IMAGE_DIR / "level_2_handle_follow_open_90_top_frames_sheet.png"

TARGET_ANGLE = np.pi / 2.0
OPEN_SAMPLE_COUNT = 49
GRASP_FINGER = level_1.NO_OVERLAP_GRASP_FINGER


def smooth(alpha: float) -> float:
    return alpha * alpha * (3.0 - 2.0 * alpha)


def body_pose(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> tuple[np.ndarray, np.ndarray]:
    body_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    return data.xpos[body_id].copy(), data.xmat[body_id].reshape(3, 3).copy()


def set_vector(model: mujoco.MjModel, data: mujoco.MjData, vector: np.ndarray, hinge: float) -> None:
    cab.set_scene_qpos(model, data, vector[:3], vector[3:], GRASP_FINGER, right_hinge_angle=hinge)


def joint_bounds(model: mujoco.MjModel) -> tuple[np.ndarray, np.ndarray]:
    lower = [3.45, 1.55, -1.20]
    upper = [4.85, 3.15, 1.20]
    for index in range(1, 8):
        joint_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, f"joint{index}")
        lower.append(float(model.jnt_range[joint_id, 0]) + 1e-4)
        upper.append(float(model.jnt_range[joint_id, 1]) - 1e-4)
    return np.asarray(lower), np.asarray(upper)


def solve_follow_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    hinge: float,
    previous: np.ndarray,
    desired_hand_pos: np.ndarray,
    desired_hand_rot: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> tuple[np.ndarray, dict]:
    scale = np.array([0.20, 0.20, 0.35, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45])

    def residual(vector: np.ndarray) -> np.ndarray:
        set_vector(model, data, vector, hinge)
        hand_pos, hand_rot = body_pose(model, data, "hand")
        position_error = hand_pos - desired_hand_pos
        rotation_error = Rotation.from_matrix(desired_hand_rot.T @ hand_rot).as_rotvec()
        continuity = (vector - previous) / scale
        return np.concatenate((position_error * 80.0, rotation_error * 24.0, continuity * 0.035))

    result = least_squares(
        residual,
        np.clip(previous, lower, upper),
        bounds=(lower, upper),
        xtol=1e-11,
        ftol=1e-11,
        gtol=1e-11,
        max_nfev=700,
    )
    solved = result.x
    set_vector(model, data, solved, hinge)
    hand_pos, hand_rot = body_pose(model, data, "hand")
    position_error = float(np.linalg.norm(hand_pos - desired_hand_pos))
    rotation_error = float(np.linalg.norm(Rotation.from_matrix(desired_hand_rot.T @ hand_rot).as_rotvec()))
    return solved, {
        "ik_success": bool(result.success),
        "ik_cost": float(result.cost),
        "hand_position_error": position_error,
        "hand_rotation_error": rotation_error,
        "function_evaluations": int(result.nfev),
    }


def combined_sample(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    phase: str,
    step_index: int,
    hinge: float,
    ik: dict | None = None,
) -> dict:
    numeric = open90.sample_state(model, data, hinge)
    visual = level_1.sample_state(model, data, phase, step_index)
    return {
        "phase": phase,
        "step_index": step_index,
        **numeric,
        "finger_contact_bodies": visual["finger_contact_bodies"],
        "forbidden_handle_contact_count": visual["forbidden_contact_count"],
        "forbidden_handle_contacts": visual["forbidden_contacts"],
        "visual_overlap_count": visual["visual_overlap_count"],
        "visual_overlaps": visual["visual_overlaps"],
        **(ik or {}),
    }


def append_motion_segment(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    frames: list[Image.Image],
    top_frames: list[Image.Image],
    start_base: np.ndarray,
    end_base: np.ndarray,
    start_q: np.ndarray,
    end_q: np.ndarray,
    start_finger: float,
    end_finger: float,
    steps: int,
    frame_stride: int,
) -> None:
    for index, raw_alpha in enumerate(np.linspace(0.0, 1.0, steps)):
        alpha = smooth(float(raw_alpha))
        base = (1.0 - alpha) * start_base + alpha * end_base
        qpos = (1.0 - alpha) * start_q + alpha * end_q
        finger = (1.0 - alpha) * start_finger + alpha * end_finger
        cab.set_scene_qpos(model, data, base, qpos, finger, right_hinge_angle=0.0)
        if index % frame_stride == 0:
            frames.append(Image.fromarray(minimal.render(model, data, "diag")))
            top_frames.append(Image.fromarray(minimal.render(model, data, "top")))


def save_frame_sheet(frames: list[Image.Image], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    chosen = frames[:: max(1, len(frames) // 12)][:12]
    thumb_w, thumb_h = 410, 310
    rows = int(np.ceil(len(chosen) / 3.0))
    sheet = Image.new("RGB", (thumb_w * 3, thumb_h * max(1, rows)), (20, 24, 28))
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(chosen):
        thumb = frame.resize((thumb_w, thumb_h))
        x = (index % 3) * thumb_w
        y = (index // 3) * thumb_h
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + 100, y + 24), fill=(0, 0, 0))
        draw.text((x + 6, y + 5), f"frame_{index:03d}", fill=(255, 255, 255))
    sheet.save(path)


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    minimal.ensure_minimal_task_xml()

    model = mujoco.MjModel.from_xml_path(str(minimal.TASK_XML))
    data = mujoco.MjData(model)
    lower, upper = joint_bounds(model)
    frames: list[Image.Image] = []
    top_frames: list[Image.Image] = []

    cab.set_scene_qpos(model, data, cab.MOBILE_BASE_START, cab.PANDA_HOME, cab.FINGER_OPEN_START, 0.0)
    frames.append(Image.fromarray(minimal.render(model, data, "diag")))
    top_frames.append(Image.fromarray(minimal.render(model, data, "top")))

    append_motion_segment(
        model, data, frames, top_frames,
        cab.MOBILE_BASE_START, level_1.NO_OVERLAP_GRASP_BASE,
        cab.PANDA_HOME, cab.PANDA_HOME,
        cab.FINGER_OPEN_START, cab.FINGER_OPEN_START,
        80, 10,
    )
    current_q = cab.PANDA_HOME.copy()
    for next_q in level_1.NO_OVERLAP_Q_PATH[1:]:
        append_motion_segment(
            model, data, frames, top_frames,
            level_1.NO_OVERLAP_GRASP_BASE, level_1.NO_OVERLAP_GRASP_BASE,
            current_q, next_q,
            cab.FINGER_OPEN_START, cab.FINGER_OPEN_START,
            95, 7,
        )
        current_q = next_q.copy()
    append_motion_segment(
        model, data, frames, top_frames,
        level_1.NO_OVERLAP_GRASP_BASE, level_1.NO_OVERLAP_GRASP_BASE,
        current_q, current_q,
        cab.FINGER_OPEN_START, GRASP_FINGER,
        80, 6,
    )

    start_vector = np.concatenate((level_1.NO_OVERLAP_GRASP_BASE, level_1.NO_OVERLAP_Q_PATH[-1]))
    set_vector(model, data, start_vector, 0.0)
    door_pos_0, door_rot_0 = body_pose(model, data, "cabinet_right_door")
    hand_pos_0, hand_rot_0 = body_pose(model, data, "hand")
    door_to_hand_pos = door_rot_0.T @ (hand_pos_0 - door_pos_0)
    door_to_hand_rot = door_rot_0.T @ hand_rot_0

    solved_rows: list[dict] = []
    open_samples: list[dict] = []
    previous = start_vector.copy()
    for index, raw_alpha in enumerate(np.linspace(0.0, 1.0, OPEN_SAMPLE_COUNT)):
        hinge = TARGET_ANGLE * smooth(float(raw_alpha))

        # Move the door first, then derive the desired hand pose from the fixed
        # Door-to-hand transform captured at the accepted Level 1 grasp.
        set_vector(model, data, previous, hinge)
        door_pos, door_rot = body_pose(model, data, "cabinet_right_door")
        desired_hand_pos = door_pos + door_rot @ door_to_hand_pos
        desired_hand_rot = door_rot @ door_to_hand_rot
        solved, ik = solve_follow_pose(
            model, data, hinge, previous, desired_hand_pos, desired_hand_rot, lower, upper
        )
        previous = solved
        state = combined_sample(model, data, "rigid_handle_follow", index, hinge, ik)
        open_samples.append(state)
        solved_rows.append({
            "hinge": float(hinge),
            "base": solved[:3].tolist(),
            "panda_qpos": solved[3:].tolist(),
            **ik,
        })
        frames.append(Image.fromarray(minimal.render(model, data, "diag")))
        top_frames.append(Image.fromarray(minimal.render(model, data, "top")))

    frames[0].save(GIF_PATH, save_all=True, append_images=frames[1:], duration=92, loop=0)
    top_frames[0].save(TOP_GIF_PATH, save_all=True, append_images=top_frames[1:], duration=92, loop=0)
    save_frame_sheet(frames, FRAME_SHEET_PATH)
    save_frame_sheet(top_frames, TOP_FRAME_SHEET_PATH)
    TRAJECTORY_PATH.write_text(json.dumps(solved_rows, indent=2) + "\n", encoding="utf-8")

    max_distance = max(item["gripper_to_handle_distance"] for item in open_samples)
    min_contacts = min(item["handle_unique_finger_contacts"] for item in open_samples)
    visual_failures = [item for item in open_samples if item["visual_overlap_count"] > 0]
    forbidden_failures = [item for item in open_samples if item["forbidden_handle_contact_count"] > 0]
    door_failures = [item for item in open_samples if item["forbidden_door_slab_contact_count"] > 0]
    max_position_error = max(item["hand_position_error"] for item in open_samples)
    max_rotation_error = max(item["hand_rotation_error"] for item in open_samples)
    final_sample = open_samples[-1]
    passed = bool(
        abs(final_sample["hinge"] - TARGET_ANGLE) <= 0.01
        and max_distance <= 0.07
        and min_contacts >= 2
        and not visual_failures
        and not forbidden_failures
        and not door_failures
        and max_position_error <= 0.002
        and max_rotation_error <= 0.01
    )
    summary = {
        "task_name": "level_2_handle_follow_open_90",
        "scope": "accepted Level 1 grasp followed rigidly with the cabinet door to 90 degrees",
        "passed_full_validation": passed,
        "target_hinge_angle": TARGET_ANGLE,
        "final_hinge_angle": final_sample["hinge"],
        "open_sample_count": len(open_samples),
        "max_gripper_to_handle_distance": max_distance,
        "min_handle_unique_finger_contacts": min_contacts,
        "max_hand_position_error": max_position_error,
        "max_hand_rotation_error": max_rotation_error,
        "visual_overlap_failure_count": len(visual_failures),
        "forbidden_handle_contact_failure_count": len(forbidden_failures),
        "door_slab_contact_failure_count": len(door_failures),
        "first_visual_failures": visual_failures[:10],
        "motion_gif": str(GIF_PATH),
        "top_view_gif": str(TOP_GIF_PATH),
        "trajectory": str(TRAJECTORY_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "top_frame_sheet": str(TOP_FRAME_SHEET_PATH),
        "note": "The hand-to-door transform is fixed from the accepted Level 1 grasp; every rendered opening frame is solved and validated directly.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
