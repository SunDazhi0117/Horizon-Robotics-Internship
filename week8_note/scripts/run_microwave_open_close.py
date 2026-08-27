"""Execute, validate, and render the Week8 microwave task."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
from PIL import Image

from week7_note.task_system.executor import (
    DEFAULT_ACTIONS,
    TaskExecutor,
    load_task_config,
)

from .microwave_runtime import TASK_XML, create_microwave_runtime
from .target_approach import TargetApproachActions


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = (
    ROOT / "configs" / "microwave_open_hold_close_target_relative.yaml"
)
DEFAULT_OUTPUT_STEM = "microwave_open_hold_close_target_relative"
TARGET_ANGLE = 1.0


def _camera(
    *,
    lookat: tuple[float, float, float],
    distance: float,
    azimuth: float,
    elevation: float,
) -> mujoco.MjvCamera:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = lookat
    camera.distance = distance
    camera.azimuth = azimuth
    camera.elevation = elevation
    return camera


def _save_gif(frames: list[Image.Image], path: Path) -> None:
    if not frames:
        raise ValueError("cannot save an empty GIF")
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=92,
        loop=0,
        optimize=False,
    )


def _render_trajectory(
    model,
    adapter,
    states,
    *,
    video_path: Path,
    top_video_path: Path,
) -> tuple[int, int]:
    front_camera = _camera(
        lookat=(3.93, 3.83, 1.08),
        distance=1.55,
        azimuth=155.0,
        elevation=-18.0,
    )
    top_camera = _camera(
        lookat=(3.93, 3.82, 0.85),
        distance=2.05,
        azimuth=180.0,
        elevation=-78.0,
    )
    stride = max(1, len(states) // 150)
    selected = [
        state
        for index, state in enumerate(states)
        if index % stride == 0 or index == len(states) - 1
    ]
    front_frames: list[Image.Image] = []
    top_frames: list[Image.Image] = []
    with (
        mujoco.Renderer(model, width=760, height=570) as front_renderer,
        mujoco.Renderer(model, width=760, height=570) as top_renderer,
    ):
        for state in selected:
            adapter.apply(state)
            front_renderer.update_scene(adapter.data, camera=front_camera)
            front_frames.append(Image.fromarray(front_renderer.render()))
            top_renderer.update_scene(adapter.data, camera=top_camera)
            top_frames.append(Image.fromarray(top_renderer.render()))
    _save_gif(front_frames, video_path)
    _save_gif(top_frames, top_video_path)
    return len(front_frames), len(top_frames)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--task-xml", type=Path, default=TASK_XML)
    parser.add_argument("--output-stem", default=DEFAULT_OUTPUT_STEM)
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    config_path = arguments.config.expanduser().resolve()
    task_xml = arguments.task_xml.expanduser().resolve()
    output_stem = str(arguments.output_stem).strip()
    if not output_stem or Path(output_stem).name != output_stem:
        raise ValueError("output-stem must be a non-empty filename stem")
    result_path = ROOT / "results" / f"{output_stem}_summary.json"
    trajectory_path = ROOT / "results" / f"{output_stem}_trajectory.json"
    video_path = ROOT / "assets" / f"{output_stem}.gif"
    top_video_path = ROOT / "assets" / f"{output_stem}_top_view.gif"

    model, _, adapter, validator = create_microwave_runtime(task_xml)
    manipulation = TargetApproachActions(adapter, validator)
    registry = dict(DEFAULT_ACTIONS)
    registry.update(manipulation.action_registry())
    result = TaskExecutor(registry).execute(load_task_config(config_path))
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
    follow_samples = [
        sample
        for sample in samples
        if sample["phase"]
        in {"open_microwave_door", "close_microwave_door"}
    ]
    lost_grasp = [
        sample
        for sample in follow_samples
        if sample["active_target_unique_finger_contact_count"] < 2
    ]
    max_angle = max(
        float(state.object_joints["microwave_hinge"])
        for state in states
    )
    final = states[-1]
    max_arm_step = max(
        sample["max_joint_step_from_previous"] for sample in samples
    )

    front_frames, top_frames = _render_trajectory(
        model,
        adapter,
        states,
        video_path=video_path,
        top_video_path=top_video_path,
    )
    passed = bool(
        not overlap_failures
        and not forbidden_failures
        and not lost_grasp
        and abs(max_angle - TARGET_ANGLE) <= 1e-9
        and abs(final.object_joints["microwave_hinge"]) <= 1e-9
        and abs(final.gripper - 0.04) <= 1e-9
        and max_arm_step <= 0.15
    )
    summary = {
        "task_name": result.task_name,
        "passed": passed,
        "state_count": len(states),
        "action_count": len(result.action_ranges),
        "actions": [item.to_dict() for item in result.action_ranges],
        "environment_geom_count_checked": len(
            validator.environment_geom_ids
        ),
        "environment_visual_overlap_failure_count": len(overlap_failures),
        "forbidden_target_contact_failure_count": len(forbidden_failures),
        "lost_grasp_failure_count": len(lost_grasp),
        "maximum_microwave_hinge_angle": max_angle,
        "target_microwave_hinge_angle": TARGET_ANGLE,
        "final_microwave_hinge_angle": float(
            final.object_joints["microwave_hinge"]
        ),
        "final_gripper": final.gripper,
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
