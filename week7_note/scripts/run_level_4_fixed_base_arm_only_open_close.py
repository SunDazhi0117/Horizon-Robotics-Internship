#!/usr/bin/env python3
"""Level 4: open and close the cabinet while the mobile base stays fixed."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from week6_note.scripts import run_panda_handle_pull_minimal as minimal
from week6_note.scripts import run_panda_reach_cabinet_handle as cab
from week7_note.scripts import level_validation_helpers as validation
from week7_note.scripts import run_level_2_handle_follow_open_90 as level_2
from week7_note.scripts import run_level_3_fixed_base_arm_only_open_90 as level_3

IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

GIF_PATH = VIDEO_DIR / "level_4_fixed_base_arm_only_open_close.gif"
TOP_GIF_PATH = VIDEO_DIR / "level_4_fixed_base_arm_only_open_close_top_view.gif"
SUMMARY_PATH = RESULT_DIR / "level_4_fixed_base_arm_only_open_close_summary.json"
TRAJECTORY_PATH = RESULT_DIR / "level_4_fixed_base_arm_only_open_close_trajectory.json"
FRAME_SHEET_PATH = IMAGE_DIR / "level_4_fixed_base_arm_only_open_close_frames_sheet.png"
TOP_FRAME_SHEET_PATH = IMAGE_DIR / "level_4_fixed_base_arm_only_open_close_top_frames_sheet.png"

OPEN_HOLD_FRAMES = 10
CLOSED_HOLD_FRAMES = 10
FRAME_DURATION_MS = 92


def joint_value(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> float:
    joint_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    return float(data.qpos[int(model.jnt_qposadr[joint_id])])


def actual_base_pose(model: mujoco.MjModel, data: mujoco.MjData) -> np.ndarray:
    return np.array(
        [
            cab.MOBILE_BASE_START[0] + joint_value(model, data, "mobile_base_x"),
            cab.MOBILE_BASE_START[1] + joint_value(model, data, "mobile_base_y"),
            joint_value(model, data, "mobile_base_yaw"),
        ]
    )


def cabinet_target_ids(model: mujoco.MjModel) -> list[int]:
    cabinet_prefixes = tuple(f"{index:03d}_" for index in range(1, 11))
    names = []
    for geom_id in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""
        if name.startswith(cabinet_prefixes) or name in (
            minimal.HANDLE_SLEEVE_GEOM,
            *minimal.HANDLE_SUPPORT_GEOMS,
        ):
            names.append(name)
    return [
        minimal.obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
        for name in names
    ]


def validate_state(
    *,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    phase: str,
    step_index: int,
    hinge: float,
    qpos: np.ndarray,
    previous_qpos: np.ndarray | None,
    panda_ids: list[int],
    cabinet_ids: list[int],
) -> dict:
    sample = level_2.combined_sample(
        model,
        data,
        phase,
        step_index,
        hinge,
    )
    cabinet_overlap = validation.visual_overlap_sample(
        model,
        data,
        phase,
        step_index,
        panda_ids,
        cabinet_ids,
    )
    base_pose = actual_base_pose(model, data)
    sample.update(
        {
            "base_pose": base_pose.tolist(),
            "base_drift": float(np.linalg.norm(base_pose - level_3.FIXED_BASE)),
            "cabinet_visual_overlap_count": cabinet_overlap["visual_overlap_count"],
            "cabinet_visual_overlaps": cabinet_overlap["visual_overlaps"],
            "max_joint_step_from_previous": (
                0.0
                if previous_qpos is None
                else float(np.max(np.abs(qpos - previous_qpos)))
            ),
        }
    )
    return sample


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    minimal.ensure_minimal_task_xml()

    source_trajectory = json.loads(level_3.TRAJECTORY_PATH.read_text(encoding="utf-8"))
    if not source_trajectory:
        raise RuntimeError("Level 3 trajectory is empty")

    model = mujoco.MjModel.from_xml_path(str(minimal.TASK_XML))
    data = mujoco.MjData(model)
    panda_ids = validation.panda_geom_ids(model)
    cabinet_ids = cabinet_target_ids(model)

    sequence: list[tuple[str, dict]] = []
    sequence.extend(("opening", row) for row in source_trajectory)
    sequence.extend(("hold_open", source_trajectory[-1]) for _ in range(OPEN_HOLD_FRAMES))
    sequence.extend(("closing", row) for row in reversed(source_trajectory[:-1]))
    sequence.extend(("hold_closed", source_trajectory[0]) for _ in range(CLOSED_HOLD_FRAMES))

    frames: list[Image.Image] = []
    top_frames: list[Image.Image] = []
    samples: list[dict] = []
    saved_trajectory: list[dict] = []
    previous_qpos: np.ndarray | None = None

    for step_index, (phase, row) in enumerate(sequence):
        hinge = float(row["hinge"])
        qpos = np.asarray(row["panda_qpos"], dtype=float)
        level_3.set_arm_state(model, data, qpos, hinge)
        sample = validate_state(
            model=model,
            data=data,
            phase=phase,
            step_index=step_index,
            hinge=hinge,
            qpos=qpos,
            previous_qpos=previous_qpos,
            panda_ids=panda_ids,
            cabinet_ids=cabinet_ids,
        )
        samples.append(sample)
        saved_trajectory.append(
            {
                "phase": phase,
                "step_index": step_index,
                "hinge": hinge,
                "fixed_base": level_3.FIXED_BASE.tolist(),
                "panda_qpos": qpos.tolist(),
                "base_drift": sample["base_drift"],
                "gripper_to_handle_distance": sample["gripper_to_handle_distance"],
                "handle_unique_finger_contacts": sample["handle_unique_finger_contacts"],
                "cabinet_visual_overlap_count": sample["cabinet_visual_overlap_count"],
                "forbidden_handle_contact_count": sample["forbidden_handle_contact_count"],
                "forbidden_door_slab_contact_count": sample[
                    "forbidden_door_slab_contact_count"
                ],
                "max_joint_step_from_previous": sample["max_joint_step_from_previous"],
            }
        )
        frames.append(Image.fromarray(minimal.render(model, data, "diag")))
        top_frames.append(Image.fromarray(minimal.render(model, data, "top")))
        previous_qpos = qpos

    frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
    )
    top_frames[0].save(
        TOP_GIF_PATH,
        save_all=True,
        append_images=top_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
    )
    level_2.save_frame_sheet(frames, FRAME_SHEET_PATH)
    level_2.save_frame_sheet(top_frames, TOP_FRAME_SHEET_PATH)
    TRAJECTORY_PATH.write_text(
        json.dumps(saved_trajectory, indent=2) + "\n",
        encoding="utf-8",
    )

    max_hinge = max(item["hinge"] for item in samples)
    final_hinge = samples[-1]["hinge"]
    max_base_drift = max(item["base_drift"] for item in samples)
    max_distance = max(item["gripper_to_handle_distance"] for item in samples)
    min_contacts = min(item["handle_unique_finger_contacts"] for item in samples)
    max_joint_step = max(item["max_joint_step_from_previous"] for item in samples)
    cabinet_overlap_failures = [
        item for item in samples if item["cabinet_visual_overlap_count"] > 0
    ]
    handle_contact_failures = [
        item for item in samples if item["forbidden_handle_contact_count"] > 0
    ]
    door_collision_failures = [
        item for item in samples if item["forbidden_door_slab_contact_count"] > 0
    ]
    passed = bool(
        max_hinge >= level_3.TARGET_ANGLE - 0.01
        and abs(final_hinge) <= 0.01
        and max_base_drift <= 1e-9
        and max_distance <= 0.06
        and min_contacts >= 2
        and max_joint_step <= 0.20
        and not cabinet_overlap_failures
        and not handle_contact_failures
        and not door_collision_failures
    )

    summary = {
        "task_name": "level_4_fixed_base_arm_only_open_close",
        "scope": "hold the handle, open the cabinet to 90 degrees, and close it while the base remains fixed",
        "passed_full_validation": passed,
        "base_locked_for_entire_task": True,
        "fixed_base_pose": level_3.FIXED_BASE.tolist(),
        "maximum_base_drift": max_base_drift,
        "target_open_hinge_angle": level_3.TARGET_ANGLE,
        "maximum_hinge_angle": max_hinge,
        "final_closed_hinge_angle": final_hinge,
        "opening_sample_count": len(source_trajectory),
        "closing_sample_count": len(source_trajectory) - 1,
        "total_validated_sample_count": len(samples),
        "max_gripper_to_handle_distance": max_distance,
        "min_handle_unique_finger_contacts": min_contacts,
        "max_joint_step": max_joint_step,
        "cabinet_visual_overlap_failure_count": len(cabinet_overlap_failures),
        "forbidden_handle_contact_failure_count": len(handle_contact_failures),
        "door_slab_collision_failure_count": len(door_collision_failures),
        "motion_gif": str(GIF_PATH),
        "top_view_gif": str(TOP_GIF_PATH),
        "trajectory": str(TRAJECTORY_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "top_frame_sheet": str(TOP_FRAME_SHEET_PATH),
        "source_level_3_trajectory": str(level_3.TRAJECTORY_PATH),
        "note": "Every opening and closing state is revalidated; the close phase traverses the accepted fixed-base arm trajectory in reverse.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
