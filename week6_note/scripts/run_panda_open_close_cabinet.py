#!/usr/bin/env python3
"""Open and close the cabinet with the stable Panda handle grasp.

This demo reuses the accepted 90-degree opening waypoints, then follows the
same path in reverse to close the cabinet. It is still a scripted qpos waypoint
prototype, but it gives a clean open-close interaction without changing the
stable Week6 v1 artifacts.
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

from week6_note.scripts import run_panda_handle_pull_90_attempt as open90
from week6_note.scripts import run_panda_handle_pull_minimal as minimal
from week6_note.scripts import run_panda_reach_cabinet_handle as cab

IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

GIF_PATH = VIDEO_DIR / "panda_open_close_cabinet.gif"
SUMMARY_PATH = RESULT_DIR / "panda_open_close_cabinet_summary.json"
FRAME_SHEET_PATH = IMAGE_DIR / "panda_open_close_cabinet_frames_sheet.png"

TARGET_OPEN_ANGLE = open90.TARGET_PULL_ANGLE
GRASP_FINGER_OPENING = open90.GRASP_FINGER_OPENING
HOLD_OPEN_STEPS = 32


def append_qpos_segment(
    *,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    frames: list[Image.Image],
    samples: list[dict[str, float]],
    start_base: np.ndarray,
    end_base: np.ndarray,
    start_q: np.ndarray,
    end_q: np.ndarray,
    start_finger: float,
    end_finger: float,
    start_hinge: float,
    end_hinge: float,
    steps: int,
    validate: bool,
    view: str = "diag",
    frame_stride: int = 7,
) -> None:
    for step, raw_alpha in enumerate(np.linspace(0.0, 1.0, steps)):
        alpha = open90.smooth(float(raw_alpha))
        base = (1.0 - alpha) * start_base + alpha * end_base
        qpos = (1.0 - alpha) * start_q + alpha * end_q
        finger = (1.0 - alpha) * start_finger + alpha * end_finger
        hinge = (1.0 - alpha) * start_hinge + alpha * end_hinge
        cab.set_scene_qpos(model, data, base, qpos, finger, right_hinge_angle=hinge)
        if validate:
            samples.append(open90.sample_state(model, data, hinge))
        if step % frame_stride == 0:
            frames.append(Image.fromarray(minimal.render(model, data, view)))


def append_hold(
    *,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    frames: list[Image.Image],
    samples: list[dict[str, float]],
    waypoint: np.ndarray,
    steps: int,
    view: str = "diag",
) -> None:
    for step in range(steps):
        cab.set_scene_qpos(
            model,
            data,
            waypoint[1:4],
            waypoint[4:11],
            GRASP_FINGER_OPENING,
            right_hinge_angle=float(waypoint[0]),
        )
        samples.append(open90.sample_state(model, data, float(waypoint[0])))
        if step % 8 == 0:
            frames.append(Image.fromarray(minimal.render(model, data, view)))


def save_frame_sheet(frames: list[Image.Image]) -> None:
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
        draw.rectangle((x, y, x + 96, y + 24), fill=(0, 0, 0))
        draw.text((x + 6, y + 5), f"frame_{index:03d}", fill=(255, 255, 255))
    sheet.save(FRAME_SHEET_PATH)


def write_summary(samples: list[dict[str, float]], open_sample: dict[str, float], closed_sample: dict[str, float]) -> dict:
    max_distance = max(sample["gripper_to_handle_distance"] for sample in samples)
    max_tool_axis_z_abs = max(sample["tool_axis_z_abs"] for sample in samples)
    max_finger_z_separation = max(sample["finger_z_separation"] for sample in samples)
    min_finger_xy_separation = min(sample["finger_xy_separation"] for sample in samples)
    min_unique_contacts = min(sample["handle_unique_finger_contacts"] for sample in samples)
    max_forbidden_contacts = max(sample["forbidden_door_slab_contact_count"] for sample in samples)
    max_hinge = max(sample["hinge"] for sample in samples)
    min_hinge = min(sample["hinge"] for sample in samples)
    passed_numeric = bool(
        max_hinge >= TARGET_OPEN_ANGLE - 0.01
        and abs(closed_sample["hinge"]) <= 0.01
        and open_sample["handle_unique_finger_contacts"] >= 2
        and closed_sample["handle_unique_finger_contacts"] >= 2
        and open_sample["gripper_to_handle_distance"] <= 0.035
        and closed_sample["gripper_to_handle_distance"] <= 0.035
        and max_distance <= 0.04
        and max_tool_axis_z_abs <= 0.01
        and max_finger_z_separation <= 0.01
        and min_finger_xy_separation >= 0.035
        and max_forbidden_contacts == 0
    )
    summary = {
        "task_name": "panda_open_close_cabinet",
        "scope": "reach, grasp visible handle, open cabinet to 90 degrees, then close it again",
        "target_open_hinge_angle": TARGET_OPEN_ANGLE,
        "final_closed_hinge_angle": closed_sample["hinge"],
        "max_hinge_angle": max_hinge,
        "min_hinge_angle": min_hinge,
        "open_sample": open_sample,
        "closed_before_release_sample": closed_sample,
        "max_gripper_to_handle_distance": max_distance,
        "max_tool_axis_z_abs": max_tool_axis_z_abs,
        "max_finger_z_separation": max_finger_z_separation,
        "min_finger_xy_separation": min_finger_xy_separation,
        "grasp_finger_opening": GRASP_FINGER_OPENING,
        "min_handle_unique_finger_contacts": min_unique_contacts,
        "max_forbidden_door_slab_contact_count": max_forbidden_contacts,
        "passed_numeric": passed_numeric,
        "requires_visual_review": True,
        "motion_gif": str(GIF_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "outputs": {
            "open_diag": str(IMAGE_DIR / "panda_open_close_cabinet_open_diag.png"),
            "closed_final_diag": str(IMAGE_DIR / "panda_open_close_cabinet_closed_final_diag.png"),
            "closed_final_top": str(IMAGE_DIR / "panda_open_close_cabinet_closed_final_top.png"),
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


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
        samples=validation_samples,
        start_base=cab.MOBILE_BASE_START,
        end_base=open90.HORIZONTAL_GRASP_BASE,
        start_q=cab.PANDA_HOME,
        end_q=cab.PANDA_HOME,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=cab.FINGER_OPEN_START,
        start_hinge=0.0,
        end_hinge=0.0,
        steps=70,
        validate=False,
        frame_stride=10,
    )

    arm_current = cab.PANDA_HOME.copy()
    for joint_offset in cab.ARM_STAGE_ORDER:
        next_q = arm_current.copy()
        next_q[joint_offset] = open90.HORIZONTAL_GRASP_Q[joint_offset]
        append_qpos_segment(
            model=model,
            data=data,
            frames=frames,
            samples=validation_samples,
            start_base=open90.HORIZONTAL_GRASP_BASE,
            end_base=open90.HORIZONTAL_GRASP_BASE,
            start_q=arm_current,
            end_q=next_q,
            start_finger=cab.FINGER_OPEN_START,
            end_finger=cab.FINGER_OPEN_START,
            start_hinge=0.0,
            end_hinge=0.0,
            steps=22,
            validate=False,
            frame_stride=11,
        )
        arm_current = next_q

    append_qpos_segment(
        model=model,
        data=data,
        frames=frames,
        samples=validation_samples,
        start_base=open90.HORIZONTAL_GRASP_BASE,
        end_base=open90.HORIZONTAL_GRASP_BASE,
        start_q=open90.HORIZONTAL_GRASP_Q,
        end_q=open90.HORIZONTAL_GRASP_Q,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=GRASP_FINGER_OPENING,
        start_hinge=0.0,
        end_hinge=0.0,
        steps=42,
        validate=True,
        frame_stride=8,
    )

    for waypoint_a, waypoint_b in zip(open90.FOLLOW_90_WAYPOINTS[:-1], open90.FOLLOW_90_WAYPOINTS[1:]):
        append_qpos_segment(
            model=model,
            data=data,
            frames=frames,
            samples=validation_samples,
            start_base=waypoint_a[1:4],
            end_base=waypoint_b[1:4],
            start_q=waypoint_a[4:11],
            end_q=waypoint_b[4:11],
            start_finger=GRASP_FINGER_OPENING,
            end_finger=GRASP_FINGER_OPENING,
            start_hinge=float(waypoint_a[0]),
            end_hinge=float(waypoint_b[0]),
            steps=24,
            validate=True,
            frame_stride=7,
        )

    open_waypoint = open90.FOLLOW_90_WAYPOINTS[-1]
    cab.set_scene_qpos(
        model,
        data,
        open_waypoint[1:4],
        open_waypoint[4:11],
        GRASP_FINGER_OPENING,
        right_hinge_angle=TARGET_OPEN_ANGLE,
    )
    open_sample = open90.sample_state(model, data, TARGET_OPEN_ANGLE)
    Image.fromarray(minimal.render(model, data, "diag")).save(
        IMAGE_DIR / "panda_open_close_cabinet_open_diag.png"
    )
    append_hold(
        model=model,
        data=data,
        frames=frames,
        samples=validation_samples,
        waypoint=open_waypoint,
        steps=HOLD_OPEN_STEPS,
    )

    reversed_waypoints = open90.FOLLOW_90_WAYPOINTS[::-1]
    for waypoint_a, waypoint_b in zip(reversed_waypoints[:-1], reversed_waypoints[1:]):
        append_qpos_segment(
            model=model,
            data=data,
            frames=frames,
            samples=validation_samples,
            start_base=waypoint_a[1:4],
            end_base=waypoint_b[1:4],
            start_q=waypoint_a[4:11],
            end_q=waypoint_b[4:11],
            start_finger=GRASP_FINGER_OPENING,
            end_finger=GRASP_FINGER_OPENING,
            start_hinge=float(waypoint_a[0]),
            end_hinge=float(waypoint_b[0]),
            steps=24,
            validate=True,
            frame_stride=7,
        )

    closed_waypoint = open90.FOLLOW_90_WAYPOINTS[0]
    cab.set_scene_qpos(
        model,
        data,
        closed_waypoint[1:4],
        closed_waypoint[4:11],
        GRASP_FINGER_OPENING,
        right_hinge_angle=0.0,
    )
    closed_sample = open90.sample_state(model, data, 0.0)
    Image.fromarray(minimal.render(model, data, "diag")).save(
        IMAGE_DIR / "panda_open_close_cabinet_closed_final_diag.png"
    )
    Image.fromarray(minimal.render(model, data, "top")).save(
        IMAGE_DIR / "panda_open_close_cabinet_closed_final_top.png"
    )

    append_qpos_segment(
        model=model,
        data=data,
        frames=frames,
        samples=validation_samples,
        start_base=closed_waypoint[1:4],
        end_base=closed_waypoint[1:4],
        start_q=closed_waypoint[4:11],
        end_q=closed_waypoint[4:11],
        start_finger=GRASP_FINGER_OPENING,
        end_finger=cab.FINGER_OPEN_START,
        start_hinge=0.0,
        end_hinge=0.0,
        steps=36,
        validate=False,
        frame_stride=9,
    )

    frames.append(Image.fromarray(minimal.render(model, data, "diag")))
    frames[0].save(GIF_PATH, save_all=True, append_images=frames[1:], duration=90, loop=0)
    save_frame_sheet(frames)

    summary = write_summary(validation_samples, open_sample, closed_sample)
    print(json.dumps(summary, indent=2))
    if not summary["passed_numeric"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
