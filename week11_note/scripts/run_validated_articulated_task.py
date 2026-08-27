"""Run the Week11 printer task with full mechanism and support checks."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np

from week7_note.scripts.level_validation_helpers import geom_obb, obb_overlap
from week7_note.task_system.executor import DEFAULT_ACTIONS, TaskExecutor, load_task_config
from week9_note.scripts.run_articulated_task import _render
from week9_note.task_system import ArticulatedObjectActions, create_scenario_runtime


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--task-xml", type=Path)
    parser.add_argument("--output-stem")
    parser.add_argument("--skip-render", action="store_true")
    return parser.parse_args()


def _sequence(value: object, *, field: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be a sequence")
    return value


def _geom_id(model: mujoco.MjModel, name: object) -> int:
    geom_name = str(name).strip()
    geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
    if geom_id < 0:
        raise ValueError(f"MuJoCo geom {geom_name!r} does not exist")
    return geom_id


def _collision_geometry_report(
    model: mujoco.MjModel,
    required_names: object,
) -> tuple[list[dict], list[dict]]:
    reports: list[dict] = []
    failures: list[dict] = []
    for raw_name in _sequence(
        required_names,
        field="strict_validation.required_collision_geoms",
    ):
        name = str(raw_name).strip()
        geom_id = _geom_id(model, name)
        report = {
            "geom": name,
            "contype": int(model.geom_contype[geom_id]),
            "conaffinity": int(model.geom_conaffinity[geom_id]),
        }
        report["passed"] = bool(
            report["contype"] > 0 and report["conaffinity"] > 0
        )
        reports.append(report)
        if not report["passed"]:
            failures.append(report)
    return reports, failures


def _clearance_report(
    model: mujoco.MjModel,
    adapter,
    states,
    raw_groups: object,
) -> tuple[list[dict], int]:
    groups = []
    for raw_group in _sequence(
        raw_groups,
        field="strict_validation.clearance_groups",
    ):
        if not isinstance(raw_group, Mapping):
            raise ValueError("each clearance group must be a mapping")
        name = str(raw_group.get("name", "")).strip()
        if not name:
            raise ValueError("clearance group name cannot be empty")
        moving = [
            (str(item).strip(), _geom_id(model, item))
            for item in _sequence(
                raw_group.get("geoms"),
                field=f"clearance group {name}.geoms",
            )
        ]
        against = [
            (str(item).strip(), _geom_id(model, item))
            for item in _sequence(
                raw_group.get("against"),
                field=f"clearance group {name}.against",
            )
        ]
        groups.append((name, moving, against))

    failures: list[dict] = []
    failing_states: set[int] = set()
    for step_index, state in enumerate(states):
        adapter.apply(state)
        for group_name, moving, against in groups:
            moving_obbs = {
                name: geom_obb(model, adapter.data, geom_id)
                for name, geom_id in moving
            }
            against_obbs = {
                name: geom_obb(model, adapter.data, geom_id)
                for name, geom_id in against
            }
            for moving_name, moving_obb in moving_obbs.items():
                for fixed_name, fixed_obb in against_obbs.items():
                    overlap, margin = obb_overlap(*moving_obb, *fixed_obb)
                    if overlap:
                        failing_states.add(step_index)
                        failures.append(
                            {
                                "step_index": step_index,
                                "phase": state.phase,
                                "group": group_name,
                                "moving_geom": moving_name,
                                "other_geom": fixed_name,
                                "sat_margin": float(margin),
                            }
                        )
    return failures, len(failing_states)


def _world_bounds(obb) -> tuple[np.ndarray, np.ndarray]:
    center, rotation, half_extent = obb
    world_half_extent = np.abs(rotation) @ half_extent
    return center - world_half_extent, center + world_half_extent


def _support_report(
    model: mujoco.MjModel,
    adapter,
    states,
    raw_checks: object,
) -> tuple[list[dict], list[dict]]:
    checks = []
    for raw_check in _sequence(
        raw_checks,
        field="strict_validation.support_checks",
    ):
        if not isinstance(raw_check, Mapping):
            raise ValueError("each support check must be a mapping")
        name = str(raw_check.get("name", "")).strip()
        if not name:
            raise ValueError("support check name cannot be empty")
        moving_name = str(raw_check.get("moving_geom", "")).strip()
        moving_id = _geom_id(model, moving_name)
        supports = [
            (str(item).strip(), _geom_id(model, item))
            for item in _sequence(
                raw_check.get("support_geoms"),
                field=f"support check {name}.support_geoms",
            )
        ]
        gap_tolerance = float(raw_check.get("vertical_gap_tolerance", 1e-6))
        minimum_overlap = float(raw_check.get("minimum_xy_overlap", 1e-3))
        checks.append(
            (
                name,
                moving_name,
                moving_id,
                supports,
                gap_tolerance,
                minimum_overlap,
            )
        )

    reports: list[dict] = []
    failures: list[dict] = []
    for step_index, state in enumerate(states):
        adapter.apply(state)
        for (
            name,
            moving_name,
            moving_id,
            supports,
            gap_tolerance,
            minimum_overlap,
        ) in checks:
            moving_min, moving_max = _world_bounds(
                geom_obb(model, adapter.data, moving_id)
            )
            candidates = []
            for support_name, support_id in supports:
                support_min, support_max = _world_bounds(
                    geom_obb(model, adapter.data, support_id)
                )
                overlap_x = max(
                    0.0,
                    min(moving_max[0], support_max[0])
                    - max(moving_min[0], support_min[0]),
                )
                overlap_y = max(
                    0.0,
                    min(moving_max[1], support_max[1])
                    - max(moving_min[1], support_min[1]),
                )
                vertical_gap = float(moving_min[2] - support_max[2])
                candidates.append(
                    {
                        "support_geom": support_name,
                        "overlap_x": float(overlap_x),
                        "overlap_y": float(overlap_y),
                        "vertical_gap": vertical_gap,
                        "score": float(overlap_x * overlap_y),
                    }
                )
            best = max(candidates, key=lambda item: item["score"])
            passed = bool(
                best["overlap_x"] >= minimum_overlap
                and best["overlap_y"] >= minimum_overlap
                and abs(best["vertical_gap"]) <= gap_tolerance
            )
            report = {
                "step_index": step_index,
                "phase": state.phase,
                "check": name,
                "moving_geom": moving_name,
                "support_geom": best["support_geom"],
                "overlap_x": best["overlap_x"],
                "overlap_y": best["overlap_y"],
                "vertical_gap": best["vertical_gap"],
                "passed": passed,
            }
            reports.append(report)
            if not passed:
                failures.append(report)
    return reports, failures


def _joint_goal_report(states, raw_goals: object) -> tuple[list[dict], bool]:
    reports = []
    passed = True
    final = states[-1]
    for raw_goal in _sequence(raw_goals, field="evaluation.joint_goals"):
        if not isinstance(raw_goal, Mapping):
            raise ValueError("each joint goal must be a mapping")
        joint_name = str(raw_goal.get("joint_name", "")).strip()
        reached = float(raw_goal.get("reached"))
        final_value = float(raw_goal.get("final", 0.0))
        values = [float(state.object_joints[joint_name]) for state in states]
        reached_error = min(abs(value - reached) for value in values)
        final_error = abs(float(final.object_joints[joint_name]) - final_value)
        goal_passed = reached_error <= 1e-8 and final_error <= 1e-8
        passed = passed and goal_passed
        reports.append(
            {
                "joint_name": joint_name,
                "reached": reached,
                "closest_reached_error": reached_error,
                "final": float(final.object_joints[joint_name]),
                "expected_final": final_value,
                "passed": goal_passed,
            }
        )
    return reports, passed


def main() -> None:
    arguments = _arguments()
    config_path = arguments.config.expanduser().resolve()
    config = load_task_config(config_path)
    runtime = config.get("runtime")
    evaluation = config.get("evaluation")
    strict = config.get("strict_validation")
    render_config = config.get("render")
    for name, value in (
        ("runtime", runtime),
        ("evaluation", evaluation),
        ("strict_validation", strict),
        ("render", render_config),
    ):
        if not isinstance(value, Mapping):
            raise ValueError(f"config {name} must be a mapping")

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

    model, _, adapter, validator = create_scenario_runtime(task_xml, runtime)
    manipulation = ArticulatedObjectActions(adapter, validator)
    registry = dict(DEFAULT_ACTIONS)
    registry.update(manipulation.action_registry())
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
        sample
        for sample in samples
        if sample["environment_visual_overlap_count"] > 0
    ]
    forbidden_failures = [
        sample
        for sample in samples
        if sample["forbidden_active_target_contact_count"] > 0
    ]
    follow_phases = {
        str(action.get("phase", action.get("action", "")))
        for action in config.get("actions", [])
        if isinstance(action, Mapping)
        and action.get("action") in {"follow_hinge_joint", "follow_slide_joint"}
    }
    lost_grasp = [
        sample
        for sample in samples
        if sample["phase"] in follow_phases
        and sample["active_target_unique_finger_contact_count"] < 2
    ]

    goal_reports, goals_passed = _joint_goal_report(
        states,
        evaluation.get("joint_goals"),
    )
    collision_reports, collision_failures = _collision_geometry_report(
        model,
        strict.get("required_collision_geoms"),
    )
    clearance_failures, clearance_failure_states = _clearance_report(
        model,
        adapter,
        states,
        strict.get("clearance_groups"),
    )
    support_reports, support_failures = _support_report(
        model,
        adapter,
        states,
        strict.get("support_checks"),
    )

    final = states[-1]
    final_gripper = float(evaluation.get("final_gripper", 0.04))
    max_step_limit = float(evaluation.get("max_arm_joint_step", 0.15))
    max_arm_step = max(sample["max_joint_step_from_previous"] for sample in samples)
    passed = bool(
        not overlap_failures
        and not forbidden_failures
        and not lost_grasp
        and goals_passed
        and not collision_failures
        and not clearance_failures
        and not support_failures
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
        "acceptance_scope": "robot, articulated mechanisms, visual collision geometry, tray support, and final restoration",
        "state_count": len(states),
        "action_count": len(result.action_ranges),
        "actions": [item.to_dict() for item in result.action_ranges],
        "joint_goals": goal_reports,
        "final_gripper": final.gripper,
        "environment_visual_overlap_failure_count": len(overlap_failures),
        "forbidden_target_contact_failure_count": len(forbidden_failures),
        "lost_grasp_failure_count": len(lost_grasp),
        "required_collision_geometry_count": len(collision_reports),
        "noncolliding_visual_geometry_failure_count": len(collision_failures),
        "mechanism_clearance_failure_count": len(clearance_failures),
        "mechanism_clearance_failure_state_count": clearance_failure_states,
        "mechanism_clearance_failures_sample": clearance_failures[:20],
        "support_check_sample_count": len(support_reports),
        "support_failure_count": len(support_failures),
        "support_failures_sample": support_failures[:20],
        "maximum_arm_joint_step": max_arm_step,
        "front_video_frame_count": frame_counts[0],
        "top_video_frame_count": frame_counts[1],
        "config": str(config_path),
        "task_xml": str(task_xml),
        "trajectory": str(trajectory_path),
        "front_video": None if asset_paths[0] is None else str(asset_paths[0]),
        "top_video": None if asset_paths[1] is None else str(asset_paths[1]),
    }
    result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
