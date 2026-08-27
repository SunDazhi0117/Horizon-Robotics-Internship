#!/usr/bin/env python3
"""Evaluate Level 4 with a local RoboDojo-style binary rubric."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = (
    ROOT
    / "assets"
    / "results"
    / "level_4_fixed_base_arm_only_open_close_summary.json"
)
OUTPUT_PATH = (
    ROOT
    / "assets"
    / "results"
    / "level_4_fixed_base_arm_only_open_close_evaluation.json"
)

MIN_OPEN_ANGLE = math.radians(85.0)
MAX_FINAL_CLOSED_ANGLE = math.radians(5.0)
MAX_BASE_DRIFT = 1e-9
MAX_GRIPPER_DISTANCE = 0.06
MAX_JOINT_STEP = 0.20


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    checks = {
        "door_opened_at_least_85_deg": (
            summary["maximum_hinge_angle"] >= MIN_OPEN_ANGLE
        ),
        "door_closed_back_below_5_deg": (
            abs(summary["final_closed_hinge_angle"]) <= MAX_FINAL_CLOSED_ANGLE
        ),
        "mobile_base_remained_fixed": (
            summary["base_locked_for_entire_task"]
            and summary["maximum_base_drift"] <= MAX_BASE_DRIFT
        ),
        "both_fingers_contacted_handle_throughout": (
            summary["min_handle_unique_finger_contacts"] >= 2
        ),
        "gripper_remained_near_handle": (
            summary["max_gripper_to_handle_distance"] <= MAX_GRIPPER_DISTANCE
        ),
        "arm_motion_remained_continuous": (
            summary["max_joint_step"] <= MAX_JOINT_STEP
        ),
        "no_whole_cabinet_visual_overlap": (
            summary["cabinet_visual_overlap_failure_count"] == 0
        ),
        "no_forbidden_handle_contact": (
            summary["forbidden_handle_contact_failure_count"] == 0
        ),
        "no_door_slab_collision": (
            summary["door_slab_collision_failure_count"] == 0
        ),
    }
    single_episode_success = all(checks.values())

    result = {
        "evaluation_name": "level_4_fixed_base_arm_only_open_close_local_evaluation",
        "task_name": "fixed_base_open_and_close_cabinet_door",
        "instruction": (
            "Keep the mobile base fixed, hold the right-door handle, open the "
            "cabinet to 90 degrees, and close it again."
        ),
        "description": (
            "The Panda uses only its seven arm joints while both fingers remain "
            "on the handle throughout a complete open-close cycle."
        ),
        "platform": "MuJoCo local simulation",
        "category": "Long-Horizon (primary), Precision (secondary)",
        "data_source": "Validated scripted arm-only kinematic trajectory",
        "usage": "Local deterministic evaluation only",
        "adapted_scoring": {
            "0": (
                "The door does not open to at least 85 degrees, does not close "
                "below 5 degrees, the base moves, the grasp is lost, or any "
                "forbidden overlap/collision occurs."
            ),
            "100": (
                "The fixed-base arm completes the open-close cycle while both "
                "fingers retain the handle and every safety gate passes."
            ),
        },
        "local_single_episode_score": 100 if single_episode_success else 0,
        "local_single_episode_success": single_episode_success,
        "checks": checks,
        "measured_values": {
            "maximum_hinge_angle_rad": summary["maximum_hinge_angle"],
            "maximum_hinge_angle_deg": math.degrees(
                summary["maximum_hinge_angle"]
            ),
            "final_closed_hinge_angle_rad": summary[
                "final_closed_hinge_angle"
            ],
            "final_closed_hinge_angle_deg": math.degrees(
                summary["final_closed_hinge_angle"]
            ),
            "maximum_base_drift": summary["maximum_base_drift"],
            "total_validated_sample_count": summary[
                "total_validated_sample_count"
            ],
            "max_gripper_to_handle_distance_m": summary[
                "max_gripper_to_handle_distance"
            ],
            "minimum_unique_finger_contacts": summary[
                "min_handle_unique_finger_contacts"
            ],
            "max_joint_step_rad": summary["max_joint_step"],
            "cabinet_visual_overlap_failure_count": summary[
                "cabinet_visual_overlap_failure_count"
            ],
            "forbidden_handle_contact_failure_count": summary[
                "forbidden_handle_contact_failure_count"
            ],
            "door_slab_collision_failure_count": summary[
                "door_slab_collision_failure_count"
            ],
        },
        "robodojo_official_status": {
            "official_score": None,
            "eligible_as_official_result": False,
            "reasons": [
                "This is a custom fixed-base cabinet open-close task.",
                "The run uses MuJoCo rather than the official Isaac Sim evaluation environment.",
                "The motion is a scripted kinematic trajectory rather than a closed-loop policy.",
                "Only one deterministic episode was evaluated without scene randomization.",
            ],
        },
        "capability_coverage": {
            "precision": "demonstrated in one fixed scene and initial state",
            "long_horizon": "demonstrated across grasp retention, opening, and closing stages",
            "generalization": "not evaluated",
            "memory": "not evaluated",
            "open_vocabulary_instruction_following": "not evaluated",
        },
        "source_summary": str(SUMMARY_PATH),
    }

    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    if not single_episode_success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
