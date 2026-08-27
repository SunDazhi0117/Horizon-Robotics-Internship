#!/usr/bin/env python3
"""Level 1: approach and grasp the cabinet handle without visual overlap.

This task uses a small RRT-found joint path to avoid the visual hand/handle
overlap seen in an earlier attempt. It isolates the grasp stage; it does not open the
cabinet yet.
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
from week7_note.scripts import level_validation_helpers as validation

IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

GIF_PATH = VIDEO_DIR / "level_1_handle_grasp.gif"
TOP_GIF_PATH = VIDEO_DIR / "level_1_handle_grasp_top_view.gif"
SUMMARY_PATH = RESULT_DIR / "level_1_handle_grasp_summary.json"
FRAME_SHEET_PATH = IMAGE_DIR / "level_1_handle_grasp_frames_sheet.png"
TOP_FRAME_SHEET_PATH = IMAGE_DIR / "level_1_handle_grasp_top_frames_sheet.png"

NO_OVERLAP_GRASP_BASE = np.array([4.361223633, 2.750938828, -0.376700703])
NO_OVERLAP_GRASP_FINGER = 0.023711985

NO_OVERLAP_Q_PATH = np.array(
    [
        [0.000000, -0.550000, 0.000000, -2.250000, 0.000000, 1.750000, 0.780000],
        [1.468353, 1.108169, -2.187055, -2.549251, 0.464016, 3.272342, 0.919151],
        [1.227116286, 1.032078802, -2.260929000, -2.372522728, 0.889101754, 3.169459233, 0.616965242],
    ],
    dtype=float,
)


def smooth(alpha: float) -> float:
    return alpha * alpha * (3.0 - 2.0 * alpha)


def visual_overlap_records(model: mujoco.MjModel, data: mujoco.MjData, phase: str, step_index: int) -> list[dict]:
    panda_ids = validation.panda_geom_ids(model)
    target_ids = validation.target_geom_ids(model)
    sample = validation.visual_overlap_sample(
        model,
        data,
        phase,
        step_index,
        panda_ids,
        target_ids,
    )
    return sample["visual_overlaps"]


def sample_state(model: mujoco.MjModel, data: mujoco.MjData, phase: str, step_index: int) -> dict:
    contact_sample = validation.contact_sample(model, data, phase, step_index)
    visual_overlaps = visual_overlap_records(model, data, phase, step_index)
    return {
        **contact_sample,
        "visual_overlap_count": len(visual_overlaps),
        "visual_overlaps": visual_overlaps,
    }


def append_segment(
    *,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    frames: list[Image.Image],
    top_frames: list[Image.Image],
    samples: list[dict],
    phase: str,
    start_base: np.ndarray,
    end_base: np.ndarray,
    start_q: np.ndarray,
    end_q: np.ndarray,
    start_finger: float,
    end_finger: float,
    steps: int,
    frame_stride: int,
) -> None:
    for step_index, raw_alpha in enumerate(np.linspace(0.0, 1.0, steps)):
        alpha = smooth(float(raw_alpha))
        base = (1.0 - alpha) * start_base + alpha * end_base
        qpos = (1.0 - alpha) * start_q + alpha * end_q
        finger = (1.0 - alpha) * start_finger + alpha * end_finger
        cab.set_scene_qpos(model, data, base, qpos, finger, right_hinge_angle=0.0)
        samples.append(sample_state(model, data, phase, step_index))
        if step_index % frame_stride == 0:
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


def write_summary(samples: list[dict]) -> dict:
    forbidden_contacts = [
        contact
        for sample in samples
        for contact in sample["forbidden_contacts"]
    ]
    visual_overlaps = [
        overlap
        for sample in samples
        for overlap in sample["visual_overlaps"]
    ]
    final_sample = samples[-1]
    passed = bool(
        len(forbidden_contacts) == 0
        and len(visual_overlaps) == 0
        and set(final_sample["finger_contact_bodies"]) == {"left_finger", "right_finger"}
        and final_sample["gripper_to_handle_distance"] <= 0.07
        and final_sample["finger_z_separation"] <= 0.01
    )
    summary = {
        "task_name": "level_1_handle_grasp",
        "scope": "approach and grasp cabinet handle with no contact or visual overlap from non-finger robot geometry",
        "passed_no_visual_overlap_grasp_validation": passed,
        "sample_count": len(samples),
        "forbidden_handle_contact_event_count": len(forbidden_contacts),
        "visual_overlap_event_count": len(visual_overlaps),
        "final_sample": final_sample,
        "max_gripper_to_handle_distance": max(sample["gripper_to_handle_distance"] for sample in samples),
        "max_finger_z_separation": max(sample["finger_z_separation"] for sample in samples),
        "motion_gif": str(GIF_PATH),
        "top_view_gif": str(TOP_GIF_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "top_frame_sheet": str(TOP_FRAME_SHEET_PATH),
        "note": "This is the current no-visual-overlap grasp subtask. It does not open the cabinet yet.",
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
    top_frames: list[Image.Image] = []
    samples: list[dict] = []

    cab.set_scene_qpos(model, data, cab.MOBILE_BASE_START, cab.PANDA_HOME, cab.FINGER_OPEN_START, 0.0)
    frames.append(Image.fromarray(minimal.render(model, data, "diag")))
    top_frames.append(Image.fromarray(minimal.render(model, data, "top")))
    samples.append(sample_state(model, data, "start", 0))

    append_segment(
        model=model,
        data=data,
        frames=frames,
        top_frames=top_frames,
        samples=samples,
        phase="base_move_to_no_overlap_station",
        start_base=cab.MOBILE_BASE_START,
        end_base=NO_OVERLAP_GRASP_BASE,
        start_q=cab.PANDA_HOME,
        end_q=cab.PANDA_HOME,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=cab.FINGER_OPEN_START,
        steps=80,
        frame_stride=10,
    )

    for path_index, (start_q, end_q) in enumerate(zip(NO_OVERLAP_Q_PATH[:-1], NO_OVERLAP_Q_PATH[1:])):
        append_segment(
            model=model,
            data=data,
            frames=frames,
            top_frames=top_frames,
            samples=samples,
            phase=f"rrt_joint_path_{path_index}",
            start_base=NO_OVERLAP_GRASP_BASE,
            end_base=NO_OVERLAP_GRASP_BASE,
            start_q=start_q,
            end_q=end_q,
            start_finger=cab.FINGER_OPEN_START,
            end_finger=cab.FINGER_OPEN_START,
            steps=95,
            frame_stride=7,
        )

    final_q = NO_OVERLAP_Q_PATH[-1]
    append_segment(
        model=model,
        data=data,
        frames=frames,
        top_frames=top_frames,
        samples=samples,
        phase="close_fingers_no_visual_overlap",
        start_base=NO_OVERLAP_GRASP_BASE,
        end_base=NO_OVERLAP_GRASP_BASE,
        start_q=final_q,
        end_q=final_q,
        start_finger=cab.FINGER_OPEN_START,
        end_finger=NO_OVERLAP_GRASP_FINGER,
        steps=80,
        frame_stride=6,
    )

    cab.set_scene_qpos(
        model,
        data,
        NO_OVERLAP_GRASP_BASE,
        final_q,
        NO_OVERLAP_GRASP_FINGER,
        right_hinge_angle=0.0,
    )
    Image.fromarray(minimal.render(model, data, "diag")).save(
        IMAGE_DIR / "level_1_handle_grasp_final_diag.png"
    )
    Image.fromarray(minimal.render(model, data, "top")).save(
        IMAGE_DIR / "level_1_handle_grasp_final_top.png"
    )
    frames.append(Image.fromarray(minimal.render(model, data, "diag")))
    top_frames.append(Image.fromarray(minimal.render(model, data, "top")))
    frames[0].save(GIF_PATH, save_all=True, append_images=frames[1:], duration=95, loop=0)
    top_frames[0].save(TOP_GIF_PATH, save_all=True, append_images=top_frames[1:], duration=95, loop=0)
    save_frame_sheet(frames, FRAME_SHEET_PATH)
    save_frame_sheet(top_frames, TOP_FRAME_SHEET_PATH)

    summary = write_summary(samples)
    print(json.dumps(summary, indent=2))
    if not summary["passed_no_visual_overlap_grasp_validation"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
