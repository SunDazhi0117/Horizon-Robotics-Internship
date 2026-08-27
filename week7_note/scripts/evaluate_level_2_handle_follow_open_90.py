#!/usr/bin/env python3
"""Evaluate Level 2 with an adapted RoboDojo-style binary rubric."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "assets" / "results" / "level_2_handle_follow_open_90_summary.json"
OUTPUT_PATH = ROOT / "assets" / "results" / "level_2_handle_follow_open_90_evaluation.json"

MIN_OPEN_ANGLE = math.radians(85.0)
MAX_GRIPPER_DISTANCE = 0.06
MAX_POSITION_ERROR = 0.002
MAX_ROTATION_ERROR = 0.01


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    checks = {
        "door_opened_at_least_85_deg": summary["final_hinge_angle"] >= MIN_OPEN_ANGLE,
        "both_fingers_contact_handle_throughout": summary["min_handle_unique_finger_contacts"] >= 2,
        "gripper_remains_near_handle": summary["max_gripper_to_handle_distance"] <= MAX_GRIPPER_DISTANCE,
        "hand_pose_tracking_is_accurate": (
            summary["max_hand_position_error"] <= MAX_POSITION_ERROR
            and summary["max_hand_rotation_error"] <= MAX_ROTATION_ERROR
        ),
        "no_visual_overlap": summary["visual_overlap_failure_count"] == 0,
        "no_forbidden_handle_contact": summary["forbidden_handle_contact_failure_count"] == 0,
        "no_door_slab_collision": summary["door_slab_contact_failure_count"] == 0,
    }
    single_episode_success = all(checks.values())

    result = {
        "evaluation_name": "level_2_handle_follow_open_90_local_evaluation",
        "task_name": "open_cabinet_door_to_90_degrees",
        "instruction": "Move to the cabinet, grasp the right-door handle, and open the cabinet door to 90 degrees.",
        "description": "The mobile Panda approaches the cabinet, grasps the vertical handle with both fingers, and follows the moving handle until the right door reaches 90 degrees.",
        "platform": "MuJoCo local simulation",
        "category": "Precision (primary), Long-Horizon (secondary)",
        "data_source": "Scripted inverse-kinematics trajectory",
        "usage": "Local deterministic evaluation only",
        "adapted_scoring": {
            "0": "The door does not reach 85 degrees, the grasp is lost, or a forbidden overlap/collision occurs.",
            "100": "The door reaches at least 85 degrees while both fingers retain the handle and all collision/overlap gates pass.",
        },
        "local_single_episode_score": 100 if single_episode_success else 0,
        "local_single_episode_success": single_episode_success,
        "checks": checks,
        "measured_values": {
            "final_hinge_angle_rad": summary["final_hinge_angle"],
            "final_hinge_angle_deg": math.degrees(summary["final_hinge_angle"]),
            "open_sample_count": summary["open_sample_count"],
            "max_gripper_to_handle_distance_m": summary["max_gripper_to_handle_distance"],
            "minimum_unique_finger_contacts": summary["min_handle_unique_finger_contacts"],
            "max_hand_position_error_m": summary["max_hand_position_error"],
            "max_hand_rotation_error_rad": summary["max_hand_rotation_error"],
            "visual_overlap_failure_count": summary["visual_overlap_failure_count"],
            "forbidden_handle_contact_failure_count": summary["forbidden_handle_contact_failure_count"],
            "door_slab_contact_failure_count": summary["door_slab_contact_failure_count"],
        },
        "robodojo_official_status": {
            "official_score": None,
            "eligible_as_official_result": False,
            "reasons": [
                "This cabinet-opening task is not one of the current official 42 RoboDojo simulation tasks.",
                "The run uses MuJoCo rather than the official Isaac Sim evaluation environment.",
                "The motion is a scripted IK trajectory, not a policy acting from observations in closed loop.",
                "Only one deterministic episode was evaluated; no randomized multi-episode success rate was measured.",
            ],
        },
        "capability_coverage": {
            "precision": "demonstrated in one deterministic trajectory",
            "long_horizon": "partially demonstrated through approach, grasp, and open stages",
            "generalization": "not evaluated",
            "memory": "not evaluated",
            "open_vocabulary_instruction_following": "not evaluated",
        },
        "source_summary": str(SUMMARY_PATH),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not single_episode_success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
