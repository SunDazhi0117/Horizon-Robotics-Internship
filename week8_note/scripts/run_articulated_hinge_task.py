"""Execute and evaluate a configured articulated hinge task."""

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

from .microwave_runtime import TASK_XML, create_microwave_runtime
from .target_approach import TargetApproachActions


ROOT = Path(__file__).resolve().parents[1]


def _camera(raw: Mapping[str, object]) -> mujoco.MjvCamera:
    lookat = np.asarray(raw.get("lookat"), dtype=float)
    if lookat.shape != (3,) or not np.all(np.isfinite(lookat)):
        raise ValueError("camera lookat must contain three finite values")
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = lookat
    camera.distance = float(raw.get("distance", 2.0))
    camera.azimuth = float(raw.get("azimuth", 135.0))
    camera.elevation = float(raw.get("elevation", -25.0))
    return camera


def _save_gif(
    frames: Sequence[Image.Image],
    path: Path,
    *,
    duration_ms: int,
) -> None:
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


def _render_trajectory(
    model,
    adapter,
    states,
    *,
    render_config: Mapping[str, object],
    video_path: Path,
    top_video_path: Path,
) -> tuple[int, int]:
    front_raw = render_config.get("front")
    top_raw = render_config.get("top")
    if not isinstance(front_raw, Mapping) or not isinstance(top_raw, Mapping):
        raise ValueError("render.front and render.top must be mappings")
    front_camera = _camera(front_raw)
    top_camera = _camera(top_raw)
    max_frames = max(1, int(render_config.get("max_frames", 180)))
    width = int(render_config.get("width", 760))
    height = int(render_config.get("height", 570))
    duration_ms = int(render_config.get("duration_ms", 92))
    stride = max(1, int(np.ceil(len(states) / max_frames)))
    selected = [
        state
        for index, state in enumerate(states)
        if index % stride == 0 or index == len(states) - 1
    ]
    front_frames: list[Image.Image] = []
    top_frames: list[Image.Image] = []
    with (
        mujoco.Renderer(model, width=width, height=height) as front_renderer,
        mujoco.Renderer(model, width=width, height=height) as top_renderer,
    ):
        for state in selected:
            adapter.apply(state)
            front_renderer.update_scene(adapter.data, camera=front_camera)
            front_frames.append(Image.fromarray(front_renderer.render()))
            top_renderer.update_scene(adapter.data, camera=top_camera)
            top_frames.append(Image.fromarray(top_renderer.render()))
    _save_gif(front_frames, video_path, duration_ms=duration_ms)
    _save_gif(top_frames, top_video_path, duration_ms=duration_ms)
    return len(front_frames), len(top_frames)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--task-xml", type=Path, default=TASK_XML)
    parser.add_argument("--output-stem", required=True)
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    config_path = arguments.config.expanduser().resolve()
    task_xml = arguments.task_xml.expanduser().resolve()
    output_stem = str(arguments.output_stem).strip()
    if not output_stem or Path(output_stem).name != output_stem:
        raise ValueError("output-stem must be a non-empty filename stem")

    config = load_task_config(config_path)
    evaluation = config.get("evaluation")
    render_config = config.get("render")
    if not isinstance(evaluation, Mapping):
        raise ValueError("config evaluation must be a mapping")
    if not isinstance(render_config, Mapping):
        raise ValueError("config render must be a mapping")

    joint_name = str(evaluation.get("joint_name", "")).strip()
    target_angle = float(evaluation.get("target_angle"))
    final_angle = float(evaluation.get("final_angle", 0.0))
    final_gripper = float(evaluation.get("final_gripper", 0.04))
    max_joint_step_limit = float(
        evaluation.get("max_arm_joint_step", 0.15)
    )
    if not joint_name:
        raise ValueError("evaluation.joint_name must be non-empty")

    follow_phases = {
        str(action.get("phase", "follow_hinge_joint"))
        for action in config.get("actions", [])
        if isinstance(action, Mapping)
        and action.get("action") == "follow_hinge_joint"
        and action.get("joint_name") == joint_name
    }
    if not follow_phases:
        raise ValueError("no follow_hinge_joint action matches evaluation joint")

    result_path = ROOT / "results" / f"{output_stem}_summary.json"
    trajectory_path = ROOT / "results" / f"{output_stem}_trajectory.json"
    video_path = ROOT / "assets" / f"{output_stem}.gif"
    top_video_path = ROOT / "assets" / f"{output_stem}_top_view.gif"

    model, _, adapter, validator = create_microwave_runtime(task_xml)
    manipulation = TargetApproachActions(adapter, validator)
    registry = dict(DEFAULT_ACTIONS)
    registry.update(manipulation.action_registry())
    result = TaskExecutor(registry).execute(config)
    states = list(result.states)

    samples = []
    previous = None
    for index, state in enumerate(states):
        samples.append(
            validator.validate(
                state,
                step_index=index,
                previous_state=previous,
            )
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
    lost_grasp = [
        sample
        for sample in samples
        if sample["phase"] in follow_phases
        and sample["active_target_unique_finger_contact_count"] < 2
    ]
    joint_values = [float(state.object_joints[joint_name]) for state in states]
    closest_target_error = min(abs(value - target_angle) for value in joint_values)
    final = states[-1]
    max_arm_step = max(
        sample["max_joint_step_from_previous"] for sample in samples
    )

    front_frames, top_frames = _render_trajectory(
        model,
        adapter,
        states,
        render_config=render_config,
        video_path=video_path,
        top_video_path=top_video_path,
    )
    passed = bool(
        not overlap_failures
        and not forbidden_failures
        and not lost_grasp
        and closest_target_error <= 1e-9
        and abs(float(final.object_joints[joint_name]) - final_angle) <= 1e-9
        and abs(final.gripper - final_gripper) <= 1e-9
        and max_arm_step <= max_joint_step_limit
    )
    summary = {
        "task_name": result.task_name,
        "passed": passed,
        "state_count": len(states),
        "action_count": len(result.action_ranges),
        "actions": [item.to_dict() for item in result.action_ranges],
        "evaluated_joint": joint_name,
        "target_joint_angle": target_angle,
        "closest_target_angle_error": closest_target_error,
        "final_joint_angle": float(final.object_joints[joint_name]),
        "final_gripper": final.gripper,
        "environment_geom_count_checked": len(
            validator.environment_geom_ids
        ),
        "environment_visual_overlap_failure_count": len(overlap_failures),
        "forbidden_target_contact_failure_count": len(forbidden_failures),
        "lost_grasp_failure_count": len(lost_grasp),
        "maximum_arm_joint_step": max_arm_step,
        "base_candidate_selection": getattr(
            manipulation,
            "last_base_candidate_report",
            None,
        ),
        "front_video_frame_count": front_frames,
        "top_video_frame_count": top_frames,
        "config": str(config_path),
        "task_xml": str(task_xml),
        "trajectory": str(trajectory_path),
        "front_video": str(video_path),
        "top_video": str(top_video_path),
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    trajectory_path.write_text(
        json.dumps([state.to_dict() for state in states], indent=2) + "\n",
        encoding="utf-8",
    )
    result_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
