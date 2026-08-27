#!/usr/bin/env python3
"""Evaluate Level 5 with a local deterministic long-horizon rubric."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = (
    ROOT
    / "assets"
    / "results"
    / "level_5_sequential_open_both_doors_summary.json"
)
OUTPUT_PATH = (
    ROOT
    / "assets"
    / "results"
    / "level_5_sequential_open_both_doors_evaluation.json"
)

MIN_OPEN_ANGLE = math.radians(85.0)
MAX_BASE_DRIFT_DURING_OPEN = 1e-9
MAX_GRIPPER_DISTANCE = 0.06
MAX_JOINT_STEP = 0.20


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    checks = {
        "right_door_opened_at_least_85_deg": (
            summary["final_right_hinge_angle"] >= MIN_OPEN_ANGLE
        ),
        "left_door_opened_at_least_85_deg": (
            summary["final_left_hinge_angle"] >= MIN_OPEN_ANGLE
        ),
        "right_opening_base_locked": (
            summary["right_opening_base_locked"]
            and summary["right_opening_maximum_base_drift"]
            <= MAX_BASE_DRIFT_DURING_OPEN
        ),
        "left_opening_used_controlled_base_motion": (
            summary["left_opening_uses_controlled_base_motion"]
            and summary["left_opening_base_displacement"] > 0.0
        ),
        "base_moved_only_in_planned_phases": (
            summary["base_moved_only_in_planned_phases"]
            and summary["base_motion_outside_planned_phase_count"] == 0
        ),
        "no_phantom_right_door_motion": (
            summary["right_hinge_motion_outside_open_phase_count"] == 0
        ),
        "no_phantom_left_door_motion": (
            summary["left_hinge_motion_outside_open_phase_count"] == 0
        ),
        "both_opening_trajectories_monotonic": (
            summary["right_opening_monotonic"]
            and summary["left_opening_monotonic"]
        ),
        "right_handle_two_finger_contact": (
            summary["right_min_unique_finger_contacts"] >= 2
        ),
        "left_handle_two_finger_contact": (
            summary["left_min_unique_finger_contacts"] >= 2
        ),
        "right_gripper_remained_near_handle": (
            summary["right_max_gripper_to_handle_distance"]
            <= MAX_GRIPPER_DISTANCE
        ),
        "left_gripper_remained_near_handle": (
            summary["left_max_gripper_to_handle_distance"]
            <= MAX_GRIPPER_DISTANCE
        ),
        "arm_motion_remained_continuous": (
            summary["max_joint_step"] <= MAX_JOINT_STEP
        ),
        "no_environment_furniture_visual_overlap": (
            summary["environment_visual_overlap_failure_count"] == 0
        ),
        "no_forbidden_active_handle_contact": (
            summary["forbidden_active_handle_contact_failure_count"] == 0
        ),
    }
    success = all(checks.values())
    result = {
        "evaluation_name": (
            "level_5_sequential_open_both_doors_local_evaluation"
        ),
        "task_name": "sequentially_open_both_cabinet_doors",
        "instruction": (
            "Open the right cabinet door, release and reposition safely, "
            "then open the left cabinet door."
        ),
        "platform": "MuJoCo local simulation",
        "category": "Long-Horizon (primary), Precision and Safety (secondary)",
        "data_source": "Validated scripted kinematic trajectory",
        "usage": "Local deterministic evaluation only",
        "local_single_episode_score": 100 if success else 0,
        "local_single_episode_success": success,
        "checks": checks,
        "measured_values": {
            "final_right_hinge_angle_deg": math.degrees(
                summary["final_right_hinge_angle"]
            ),
            "final_left_hinge_angle_deg": math.degrees(
                summary["final_left_hinge_angle"]
            ),
            "right_opening_maximum_base_drift": summary[
                "right_opening_maximum_base_drift"
            ],
            "left_opening_base_displacement": summary[
                "left_opening_base_displacement"
            ],
            "total_validated_sample_count": summary[
                "total_validated_sample_count"
            ],
            "right_min_unique_finger_contacts": summary[
                "right_min_unique_finger_contacts"
            ],
            "left_min_unique_finger_contacts": summary[
                "left_min_unique_finger_contacts"
            ],
            "right_max_gripper_to_handle_distance_m": summary[
                "right_max_gripper_to_handle_distance"
            ],
            "left_max_gripper_to_handle_distance_m": summary[
                "left_max_gripper_to_handle_distance"
            ],
            "max_joint_step_rad": summary["max_joint_step"],
            "environment_geom_count_checked": summary[
                "environment_geom_count_checked"
            ],
            "environment_visual_overlap_failure_count": summary[
                "environment_visual_overlap_failure_count"
            ],
            "forbidden_active_handle_contact_failure_count": summary[
                "forbidden_active_handle_contact_failure_count"
            ],
        },
        "robodojo_official_status": {
            "official_score": None,
            "eligible_as_official_result": False,
            "reasons": [
                "This is a custom double-door cabinet task.",
                "The run uses MuJoCo rather than the official evaluation environment.",
                "The motion is scripted rather than generated by a closed-loop policy.",
                "Only one deterministic scene and initial state were evaluated.",
            ],
        },
        "source_summary": str(SUMMARY_PATH),
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
