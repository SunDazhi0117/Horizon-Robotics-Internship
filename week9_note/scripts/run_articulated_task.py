"""Execute, validate, and render a configured Week9/Week10 task."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image

from week7_note.task_system.executor import (
    DEFAULT_ACTIONS,
    TaskExecutor,
    load_task_config,
)
from week9_note.task_system import (
    ArticulatedObjectActions,
    create_scenario_runtime,
)


def _camera(raw: Mapping[str, object]) -> mujoco.MjvCamera:
    lookat = np.asarray(raw.get("lookat"), dtype=float)
    if lookat.shape != (3,) or not np.all(np.isfinite(lookat)):
        raise ValueError("camera lookat must contain three finite values")
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = lookat
    camera.distance = float(raw.get("distance", 2.1))
    camera.azimuth = float(raw.get("azimuth", 135.0))
    camera.elevation = float(raw.get("elevation", -25.0))
    return camera


def _save_gif(frames: Sequence[Image.Image], path: Path, duration_ms: int) -> None:
    if not frames:
        raise ValueError("cannot save an empty GIF")
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        save_all=True,
        append_images=list(frames[1:]),
        duration=duration_ms,
        loop=0,
        optimize=False,
    )


def _render(model, adapter, states, render_config, output_root, stem):
    front_raw = render_config.get("front")
    top_raw = render_config.get("top")
    if not isinstance(front_raw, Mapping) or not isinstance(top_raw, Mapping):
        raise ValueError("render.front and render.top must be mappings")
    cameras = (_camera(front_raw), _camera(top_raw))
    max_frames = max(1, int(render_config.get("max_frames", 160)))
    width = int(render_config.get("width", 720))
    height = int(render_config.get("height", 540))
    duration_ms = int(render_config.get("duration_ms", 90))
    stride = max(1, int(np.ceil(len(states) / max_frames)))
    selected = [
        state
        for index, state in enumerate(states)
        if index % stride == 0 or index == len(states) - 1
    ]
    paths = (
        output_root / "assets" / f"{stem}.gif",
        output_root / "assets" / f"{stem}_top_view.gif",
    )
    frame_counts = []
    for camera, path in zip(cameras, paths):
        frames: list[Image.Image] = []
        with mujoco.Renderer(model, width=width, height=height) as renderer:
            for state in selected:
                adapter.apply(state)
                renderer.update_scene(adapter.data, camera=camera)
                frames.append(Image.fromarray(renderer.render()))
        _save_gif(frames, path, duration_ms)
        frame_counts.append(len(frames))
    return paths, tuple(frame_counts)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--task-xml", type=Path)
    parser.add_argument("--output-stem")
    parser.add_argument("--skip-render", action="store_true")
    return parser.parse_args()


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

    model, _, adapter, validator = create_scenario_runtime(
        task_xml,
        runtime,
    )
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
        sample for sample in samples
        if sample["environment_visual_overlap_count"] > 0
    ]
    forbidden_failures = [
        sample for sample in samples
        if sample["forbidden_active_target_contact_count"] > 0
    ]
    follow_phases = {
        str(action.get("phase", action.get("action", "")))
        for action in config.get("actions", [])
        if isinstance(action, Mapping)
        and action.get("action") in {"follow_hinge_joint", "follow_slide_joint"}
    }
    lost_grasp = [
        sample for sample in samples
        if sample["phase"] in follow_phases
        and sample["active_target_unique_finger_contact_count"] < 2
    ]

    goals_raw = evaluation.get("joint_goals")
    if not isinstance(goals_raw, Sequence) or isinstance(goals_raw, (str, bytes)):
        raise ValueError("evaluation.joint_goals must be a sequence")
    goal_reports = []
    goals_passed = True
    final = states[-1]
    for raw_goal in goals_raw:
        if not isinstance(raw_goal, Mapping):
            raise ValueError("each joint goal must be a mapping")
        joint_name = str(raw_goal.get("joint_name", "")).strip()
        reached = float(raw_goal.get("reached"))
        final_value = float(raw_goal.get("final", 0.0))
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
    result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
