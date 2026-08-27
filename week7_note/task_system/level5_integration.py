"""Adapt the accepted Level 5 trajectory to the reusable TaskState API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

from week6_note.scripts import run_panda_reach_cabinet_handle as cab
from week7_note.scripts import run_level_5_sequential_open_both_doors as level5

from .mujoco_adapter import MujocoJointMapping, MujocoStateAdapter
from .panda_validation import PandaStateValidator
from .state import TaskState


DEFAULT_RESULT_PATH = (
    level5.ROOT
    / "task_system"
    / "results"
    / "level5_taskstate_adapter_validation.json"
)


def load_level5_states(
    trajectory_path: str | Path = level5.TRAJECTORY_PATH,
) -> list[TaskState]:
    """Convert the accepted Level 5 JSON trajectory into TaskState objects."""

    path = Path(trajectory_path)
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Level 5 trajectory must be a non-empty JSON list")

    states = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"trajectory row {index} must be a mapping")
        states.append(
            TaskState(
                phase=row["phase"],
                base=row.get("commanded_base", row["base"]),
                arm_qpos=row["panda_qpos"],
                gripper=row["finger"],
                object_joints={
                    "left_hinge": row["left_hinge"],
                    "right_hinge": row["right_hinge"],
                },
                active_target=row.get("active_handle"),
            )
        )
    return states


def create_level5_runtime() -> tuple[
    mujoco.MjModel,
    mujoco.MjData,
    MujocoStateAdapter,
    PandaStateValidator,
]:
    """Create the model, data, state adapter, and validator for Level 5."""

    if not level5.TASK_XML.is_file():
        raise FileNotFoundError(
            f"Level 5 XML does not exist: {level5.TASK_XML}"
        )

    model = mujoco.MjModel.from_xml_path(str(level5.TASK_XML))
    data = mujoco.MjData(model)
    mapping = MujocoJointMapping(
        base_joints=(
            "mobile_base_x",
            "mobile_base_y",
            "mobile_base_yaw",
        ),
        arm_joints=tuple(f"joint{index}" for index in range(1, 8)),
        gripper_joints=("finger_joint1", "finger_joint2"),
        base_origin=(
            float(cab.MOBILE_BASE_START[0]),
            float(cab.MOBILE_BASE_START[1]),
            0.0,
        ),
        object_joint_aliases={
            "left_hinge": "left_hinge",
            "right_hinge": "right_hinge",
        },
    )
    adapter = MujocoStateAdapter(model, data, mapping)
    validator = PandaStateValidator(
        adapter,
        allowed_finger_target_geoms={
            level5.LEFT_HANDLE,
            level5.RIGHT_HANDLE,
        },
    )
    return model, data, adapter, validator


def validate_level5_states(
    states: list[TaskState],
    validator: PandaStateValidator,
) -> tuple[list[dict], dict]:
    """Validate Level 5 TaskStates and return samples plus summary."""

    samples: list[dict] = []
    previous: TaskState | None = None
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
    contact_failures = [
        sample
        for sample in samples
        if sample["forbidden_active_target_contact_count"] > 0
    ]
    max_base_error = max(
        sample["base_command_error"]
        for sample in samples
    )
    max_arm_error = max(
        float(
            np.max(
                np.abs(
                    np.asarray(sample["arm_qpos"])
                    - np.asarray(sample["commanded_arm_qpos"])
                )
            )
        )
        for sample in samples
    )
    max_object_joint_error = max(
        max(
            (
                abs(
                    sample["object_joints"][name]
                    - commanded_value
                )
                for name, commanded_value
                in sample["commanded_object_joints"].items()
            ),
            default=0.0,
        )
        for sample in samples
    )
    max_joint_step = max(
        sample["max_joint_step_from_previous"]
        for sample in samples
    )

    final = samples[-1]
    summary = {
        "integration_name": "level5_taskstate_mujoco_adapter",
        "passed": bool(
            not overlap_failures
            and not contact_failures
            and max_base_error <= 1e-9
            and max_arm_error <= 1e-9
            and max_object_joint_error <= 1e-9
        ),
        "state_count": len(samples),
        "environment_geom_count_checked": len(
            validator.environment_geom_ids
        ),
        "environment_visual_overlap_failure_count": len(
            overlap_failures
        ),
        "forbidden_active_target_contact_failure_count": len(
            contact_failures
        ),
        "maximum_base_roundtrip_error": max_base_error,
        "maximum_arm_roundtrip_error": max_arm_error,
        "maximum_object_joint_roundtrip_error": max_object_joint_error,
        "maximum_joint_step": max_joint_step,
        "final_object_joints": final["object_joints"],
        "source_trajectory": str(level5.TRAJECTORY_PATH),
        "source_task_xml": str(level5.TASK_XML),
    }
    return samples, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate saved Level 5 states through TaskState.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Validate only the first N states for a quick smoke test",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULT_PATH,
        help="Summary JSON output path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    states = load_level5_states()
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be at least 1")
        states = states[: args.limit]

    _, _, _, validator = create_level5_runtime()
    _, summary = validate_level5_states(states, validator)

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
