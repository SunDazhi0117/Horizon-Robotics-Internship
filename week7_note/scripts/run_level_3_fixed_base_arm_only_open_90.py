#!/usr/bin/env python3
"""Level 3: open the cabinet with the mobile base fixed after grasping.

The task begins from a validated two-finger grasp. The mobile base x/y/yaw are
frozen for the complete video. Only the seven Panda arm joints may change while
inverse kinematics follows the moving handle to 90 degrees.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from week6_note.scripts import run_panda_handle_pull_minimal as minimal
from week6_note.scripts import run_panda_reach_cabinet_handle as cab
from week7_note.scripts import run_level_1_handle_grasp as level_1
from week7_note.scripts import run_level_2_handle_follow_open_90 as level_2

IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

GIF_PATH = VIDEO_DIR / "level_3_fixed_base_arm_only_open_90.gif"
TOP_GIF_PATH = VIDEO_DIR / "level_3_fixed_base_arm_only_open_90_top_view.gif"
SUMMARY_PATH = RESULT_DIR / "level_3_fixed_base_arm_only_open_90_summary.json"
TRAJECTORY_PATH = RESULT_DIR / "level_3_fixed_base_arm_only_open_90_trajectory.json"
FRAME_SHEET_PATH = IMAGE_DIR / "level_3_fixed_base_arm_only_open_90_frames_sheet.png"
TOP_FRAME_SHEET_PATH = IMAGE_DIR / "level_3_fixed_base_arm_only_open_90_top_frames_sheet.png"

FIXED_BASE = np.array([4.49, 2.30, 0.05])
GRASP_Q = np.array(
    [
        0.087489178,
        0.349237767,
        -0.425046843,
        -1.234147529,
        -1.466619976,
        1.674814084,
        2.341326505,
    ]
)
GRASP_FINGER = level_1.NO_OVERLAP_GRASP_FINGER
TARGET_ANGLE = np.pi / 2.0
OPEN_SAMPLE_COUNT = 65


def arm_joint_bounds(model: mujoco.MjModel) -> tuple[np.ndarray, np.ndarray]:
    lower: list[float] = []
    upper: list[float] = []
    for index in range(1, 8):
        joint_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, f"joint{index}")
        lower.append(float(model.jnt_range[joint_id, 0]) + 1e-4)
        upper.append(float(model.jnt_range[joint_id, 1]) - 1e-4)
    return np.asarray(lower), np.asarray(upper)


def set_arm_state(model: mujoco.MjModel, data: mujoco.MjData, qpos: np.ndarray, hinge: float) -> None:
    cab.set_scene_qpos(
        model,
        data,
        FIXED_BASE,
        qpos,
        GRASP_FINGER,
        right_hinge_angle=hinge,
    )


def solve_arm_only_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    hinge: float,
    previous_q: np.ndarray,
    desired_hand_pos: np.ndarray,
    desired_hand_rot: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> tuple[np.ndarray, dict]:
    joint_scale = np.full(7, 0.45)

    def residual(qpos: np.ndarray) -> np.ndarray:
        set_arm_state(model, data, qpos, hinge)
        hand_pos, hand_rot = level_2.body_pose(model, data, "hand")
        position_error = hand_pos - desired_hand_pos
        rotation_error = Rotation.from_matrix(desired_hand_rot.T @ hand_rot).as_rotvec()
        continuity = (qpos - previous_q) / joint_scale
        return np.concatenate(
            (
                position_error * 100.0,
                rotation_error * 30.0,
                continuity * 0.018,
            )
        )

    result = least_squares(
        residual,
        np.clip(previous_q, lower, upper),
        bounds=(lower, upper),
        xtol=1e-12,
        ftol=1e-12,
        gtol=1e-12,
        max_nfev=1200,
    )
    solved_q = result.x
    set_arm_state(model, data, solved_q, hinge)
    hand_pos, hand_rot = level_2.body_pose(model, data, "hand")
    position_error = float(np.linalg.norm(hand_pos - desired_hand_pos))
    rotation_error = float(
        np.linalg.norm(Rotation.from_matrix(desired_hand_rot.T @ hand_rot).as_rotvec())
    )
    return solved_q, {
        "ik_success": bool(result.success),
        "ik_cost": float(result.cost),
        "hand_position_error": position_error,
        "hand_rotation_error": rotation_error,
        "function_evaluations": int(result.nfev),
    }


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    minimal.ensure_minimal_task_xml()

    model = mujoco.MjModel.from_xml_path(str(minimal.TASK_XML))
    data = mujoco.MjData(model)
    lower, upper = arm_joint_bounds(model)
    frames: list[Image.Image] = []
    top_frames: list[Image.Image] = []

    # Begin from the validated fixed-base grasp and hold it briefly on screen.
    set_arm_state(model, data, GRASP_Q, 0.0)
    initial_diag = Image.fromarray(minimal.render(model, data, "diag"))
    initial_top = Image.fromarray(minimal.render(model, data, "top"))
    frames.extend([initial_diag.copy() for _ in range(7)])
    top_frames.extend([initial_top.copy() for _ in range(7)])

    # Capture the validated grasp transform relative to the closed cabinet door.
    door_pos_0, door_rot_0 = level_2.body_pose(model, data, "cabinet_right_door")
    hand_pos_0, hand_rot_0 = level_2.body_pose(model, data, "hand")
    door_to_hand_pos = door_rot_0.T @ (hand_pos_0 - door_pos_0)
    door_to_hand_rot = door_rot_0.T @ hand_rot_0

    previous_q = GRASP_Q.copy()
    open_samples: list[dict] = []
    trajectory: list[dict] = []
    max_joint_step = 0.0

    for index, raw_alpha in enumerate(np.linspace(0.0, 1.0, OPEN_SAMPLE_COUNT)):
        hinge = TARGET_ANGLE * level_2.smooth(float(raw_alpha))

        set_arm_state(model, data, previous_q, hinge)
        door_pos, door_rot = level_2.body_pose(model, data, "cabinet_right_door")
        desired_hand_pos = door_pos + door_rot @ door_to_hand_pos
        desired_hand_rot = door_rot @ door_to_hand_rot

        solved_q, ik = solve_arm_only_pose(
            model,
            data,
            hinge,
            previous_q,
            desired_hand_pos,
            desired_hand_rot,
            lower,
            upper,
        )
        joint_step = float(np.max(np.abs(solved_q - previous_q)))
        max_joint_step = max(max_joint_step, joint_step)
        previous_q = solved_q

        sample = level_2.combined_sample(
            model,
            data,
            "fixed_base_arm_only_follow",
            index,
            hinge,
            ik,
        )
        sample["base_pose"] = FIXED_BASE.tolist()
        sample["max_joint_step_from_previous"] = joint_step
        open_samples.append(sample)
        trajectory.append(
            {
                "hinge": float(hinge),
                "fixed_base": FIXED_BASE.tolist(),
                "panda_qpos": solved_q.tolist(),
                "max_joint_step_from_previous": joint_step,
                **ik,
            }
        )
        frames.append(Image.fromarray(minimal.render(model, data, "diag")))
        top_frames.append(Image.fromarray(minimal.render(model, data, "top")))

    frames[0].save(GIF_PATH, save_all=True, append_images=frames[1:], duration=92, loop=0)
    top_frames[0].save(TOP_GIF_PATH, save_all=True, append_images=top_frames[1:], duration=92, loop=0)
    level_2.save_frame_sheet(frames, FRAME_SHEET_PATH)
    level_2.save_frame_sheet(top_frames, TOP_FRAME_SHEET_PATH)
    TRAJECTORY_PATH.write_text(json.dumps(trajectory, indent=2) + "\n", encoding="utf-8")

    max_distance = max(item["gripper_to_handle_distance"] for item in open_samples)
    min_contacts = min(item["handle_unique_finger_contacts"] for item in open_samples)
    visual_failures = [item for item in open_samples if item["visual_overlap_count"] > 0]
    forbidden_failures = [
        item for item in open_samples if item["forbidden_handle_contact_count"] > 0
    ]
    door_failures = [
        item for item in open_samples if item["forbidden_door_slab_contact_count"] > 0
    ]
    max_position_error = max(item["hand_position_error"] for item in open_samples)
    max_rotation_error = max(item["hand_rotation_error"] for item in open_samples)
    final_sample = open_samples[-1]
    passed = bool(
        abs(final_sample["hinge"] - TARGET_ANGLE) <= 0.01
        and max_distance <= 0.06
        and min_contacts >= 2
        and not visual_failures
        and not forbidden_failures
        and not door_failures
        and max_position_error <= 0.002
        and max_rotation_error <= 0.01
        and max_joint_step <= 0.20
    )
    summary = {
        "task_name": "level_3_fixed_base_arm_only_open_90",
        "scope": "validated fixed-base grasp followed to 90 degrees using only Panda arm joints",
        "passed_full_validation": passed,
        "base_locked_during_opening": True,
        "fixed_base_pose": FIXED_BASE.tolist(),
        "maximum_base_drift": 0.0,
        "target_hinge_angle": TARGET_ANGLE,
        "final_hinge_angle": final_sample["hinge"],
        "open_sample_count": len(open_samples),
        "max_gripper_to_handle_distance": max_distance,
        "min_handle_unique_finger_contacts": min_contacts,
        "max_hand_position_error": max_position_error,
        "max_hand_rotation_error": max_rotation_error,
        "max_joint_step": max_joint_step,
        "visual_overlap_failure_count": len(visual_failures),
        "forbidden_handle_contact_failure_count": len(forbidden_failures),
        "door_slab_contact_failure_count": len(door_failures),
        "first_visual_failures": visual_failures[:10],
        "motion_gif": str(GIF_PATH),
        "top_view_gif": str(TOP_GIF_PATH),
        "trajectory": str(TRAJECTORY_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "top_frame_sheet": str(TOP_FRAME_SHEET_PATH),
        "note": "The video starts from a validated two-finger grasp. Base x, y, and yaw remain fixed for every frame.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
