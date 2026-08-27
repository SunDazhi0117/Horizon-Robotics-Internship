"""Execute, validate, evaluate, and render a Week11 transfer task."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np

from week7_note.task_system.executor import (
    DEFAULT_ACTIONS,
    TaskExecutor,
    load_task_config,
)
from week9_note.scripts.run_articulated_task import _render
from week11_note.task_system import (
    PayloadTransferActions,
    create_week11_runtime,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--task-xml", type=Path)
    parser.add_argument("--output-stem")
    parser.add_argument("--skip-render", action="store_true")
    return parser.parse_args()


def _site_position(model, data, name: str) -> np.ndarray:
    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if site_id < 0:
        raise ValueError(f"MuJoCo site {name!r} does not exist")
    return data.site_xpos[site_id].copy()


def _body_position(model, data, name: str) -> np.ndarray:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if body_id < 0:
        raise ValueError(f"MuJoCo body {name!r} does not exist")
    return data.xpos[body_id].copy()


def main() -> None:
    arguments = _arguments()
    config_path = arguments.config.expanduser().resolve()
    config = load_task_config(config_path)
    runtime = config.get("runtime")
    evaluation = config.get("evaluation")
    render_config = config.get("render")
    if not isinstance(runtime, Mapping):
        raise ValueError("config runtime must be a mapping")
    if not isinstance(evaluation, Mapping):
        raise ValueError("config evaluation must be a mapping")
    if not isinstance(render_config, Mapping):
        raise ValueError("config render must be a mapping")

    project_root = config_path.parent.parent
    raw_xml = arguments.task_xml or runtime.get("task_xml")
    if raw_xml is None:
        raise ValueError("runtime.task_xml is required")
    task_xml = Path(raw_xml)
    if not task_xml.is_absolute():
        task_xml = (project_root / task_xml).resolve()
    stem = arguments.output_stem or str(config.get("task_name", "task"))
    if not stem or Path(stem).name != stem:
        raise ValueError("output stem must be a non-empty filename stem")

    model, _, adapter, validator = create_week11_runtime(task_xml, runtime)
    actions = PayloadTransferActions(adapter, validator)
    registry = dict(DEFAULT_ACTIONS)
    registry.update(actions.action_registry())
    result = TaskExecutor(registry).execute(config)
    states = list(result.states)

    samples = []
    previous = None
    for index, state in enumerate(states):
        samples.append(
            validator.validate(state, step_index=index, previous_state=previous)
        )
        previous = state
    overlap_failures = [
        sample for sample in samples
        if sample["environment_visual_overlap_count"] > 0
    ]
    forbidden_failures = [
        sample for sample in samples
        if sample["forbidden_active_target_contact_count"] > 0
    ]
    grasp_phases = {
        str(action.get("phase", action.get("action", "")))
        for action in config.get("actions", [])
        if isinstance(action, Mapping)
        and action.get("action") in {
            "follow_hinge_joint",
            "follow_slide_joint",
            "carry_payload",
        }
    }
    lost_grasp = [
        sample for sample in samples
        if sample["phase"] in grasp_phases
        and sample["active_target_unique_finger_contact_count"] < 2
    ]

    goals_raw = evaluation.get("joint_goals")
    if not isinstance(goals_raw, Sequence) or isinstance(
        goals_raw,
        (str, bytes),
    ):
        raise ValueError("evaluation.joint_goals must be a sequence")
    goal_reports = []
    goals_passed = True
    final = states[-1]
    for raw_goal in goals_raw:
        if not isinstance(raw_goal, Mapping):
            raise ValueError("each joint goal must be a mapping")
        joint_name = str(raw_goal.get("joint_name", "")).strip()
        reached = float(raw_goal.get("reached"))
        final_value = float(raw_goal.get("final", reached))
        values = [float(state.object_joints[joint_name]) for state in states]
        reached_error = min(abs(value - reached) for value in values)
        final_error = abs(float(final.object_joints[joint_name]) - final_value)
        goal_passed = reached_error <= 1e-8 and final_error <= 1e-8
        goals_passed = goals_passed and goal_passed
        goal_reports.append(
            {
                "joint_name": joint_name,
                "reached": reached,
                "closest_reached_error": reached_error,
                "final": float(final.object_joints[joint_name]),
                "expected_final": final_value,
                "passed": goal_passed,
            }
        )

    payload_raw = evaluation.get("payload_goal")
    if not isinstance(payload_raw, Mapping):
        raise ValueError("evaluation.payload_goal must be a mapping")
    adapter.apply(final)
    payload_body = str(payload_raw.get("body", "")).strip()
    destination_site = str(payload_raw.get("destination_site", "")).strip()
    destination_offset = np.asarray(
        payload_raw.get("destination_offset", (0.0, 0.0, 0.0)),
        dtype=float,
    )
    if destination_offset.shape != (3,):
        raise ValueError("payload destination_offset must have three values")
    site_position = _site_position(model, adapter.data, destination_site)
    site_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_SITE,
        destination_site,
    )
    site_rotation = adapter.data.site_xmat[site_id].reshape(3, 3)
    expected_payload = site_position + site_rotation @ destination_offset
    actual_payload = _body_position(model, adapter.data, payload_body)
    payload_error = float(np.linalg.norm(actual_payload - expected_payload))
    payload_tolerance = float(payload_raw.get("tolerance", 1e-6))
    payload_passed = payload_error <= payload_tolerance

    final_gripper = float(evaluation.get("final_gripper", 0.04))
    max_step_limit = float(evaluation.get("max_arm_joint_step", 0.15))
    max_arm_step = max(
        sample["max_joint_step_from_previous"] for sample in samples
    )
    passed = bool(
        not overlap_failures
        and not forbidden_failures
        and not lost_grasp
        and goals_passed
        and payload_passed
        and abs(final.gripper - final_gripper) <= 1e-8
        and max_arm_step <= max_step_limit
    )

    asset_paths = (None, None)
    frame_counts = (0, 0)
    if not arguments.skip_render:
        asset_paths, frame_counts = _render(
            model,
            adapter,
            states,
            render_config,
            project_root,
            stem,
        )

    result_path = project_root / "results" / f"{stem}_summary.json"
    trajectory_path = project_root / "results" / f"{stem}_trajectory.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    trajectory_path.write_text(
        json.dumps([state.to_dict() for state in states], indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "task_name": result.task_name,
        "passed": passed,
        "state_count": len(states),
        "action_count": len(result.action_ranges),
        "actions": [item.to_dict() for item in result.action_ranges],
        "joint_goals": goal_reports,
        "payload_goal": {
            "body": payload_body,
            "destination_site": destination_site,
            "actual_position": actual_payload.tolist(),
            "expected_position": expected_payload.tolist(),
            "position_error": payload_error,
            "tolerance": payload_tolerance,
            "passed": payload_passed,
        },
        "final_gripper": final.gripper,
        "environment_visual_overlap_failure_count": len(overlap_failures),
        "forbidden_target_contact_failure_count": len(forbidden_failures),
        "lost_grasp_failure_count": len(lost_grasp),
        "maximum_arm_joint_step": max_arm_step,
        "front_video_frame_count": frame_counts[0],
        "top_video_frame_count": frame_counts[1],
        "config": str(config_path),
        "task_xml": str(task_xml),
        "trajectory": str(trajectory_path),
        "front_video": None if asset_paths[0] is None else str(asset_paths[0]),
        "top_video": None if asset_paths[1] is None else str(asset_paths[1]),
    }
    result_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
