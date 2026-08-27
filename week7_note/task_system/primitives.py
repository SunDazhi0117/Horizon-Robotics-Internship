"""Reusable trajectory-building primitives.

Every primitive receives an immutable TaskState and returns only newly
generated states. The caller can concatenate those states into a task
trajectory without changing the input state.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .state import TaskState


_KEEP_TARGET = object()


def _positive_count(value: int, *, name: str, minimum: int) -> int:
    count = int(value)
    if count < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return count


def _finite_vector(
    value: np.ndarray | Sequence[float],
    *,
    name: str,
    expected_size: int,
) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.ndim != 1 or vector.size != expected_size:
        raise ValueError(f"{name} must contain {expected_size} values")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values")
    return vector


def smooth_progress(alpha: float) -> float:
    """Map linear progress to a smooth start-and-stop curve."""

    value = float(alpha)
    if not 0.0 <= value <= 1.0:
        raise ValueError("alpha must be between 0 and 1")
    return value * value * (3.0 - 2.0 * value)


def hold_pose(
    state: TaskState,
    *,
    frames: int,
    phase: str = "hold_pose",
) -> list[TaskState]:
    """Repeat a state for a fixed number of output frames."""

    frame_count = _positive_count(frames, name="frames", minimum=1)
    return [
        state.with_updates(phase=phase)
        for _ in range(frame_count)
    ]


def move_base(
    state: TaskState,
    *,
    waypoints: Sequence[np.ndarray | Sequence[float]],
    steps_per_segment: int = 31,
    phase: str = "move_base",
) -> list[TaskState]:
    """Move the base through one or more [x, y, yaw] targets.

    The input state's base is the implicit starting point. Each waypoint is a
    target, so callers do not repeat the starting base in the waypoint list.
    """

    if not waypoints:
        raise ValueError("waypoints must contain at least one target")
    steps = _positive_count(
        steps_per_segment,
        name="steps_per_segment",
        minimum=2,
    )

    generated: list[TaskState] = []
    start = state.base
    current_state = state
    for index, waypoint in enumerate(waypoints):
        end = _finite_vector(
            waypoint,
            name=f"waypoints[{index}]",
            expected_size=3,
        )
        for raw_alpha in np.linspace(0.0, 1.0, steps)[1:]:
            alpha = smooth_progress(float(raw_alpha))
            base = (1.0 - alpha) * start + alpha * end
            current_state = current_state.with_updates(
                phase=phase,
                base=base,
            )
            generated.append(current_state)
        start = end
    return generated


def move_arm(
    state: TaskState,
    *,
    waypoints: Sequence[np.ndarray | Sequence[float]],
    max_step: float = 0.045,
    phase: str = "move_arm",
) -> list[TaskState]:
    """Interpolate arm-joint waypoints with a maximum per-joint step."""

    if not waypoints:
        raise ValueError("waypoints must contain at least one target")
    step_limit = float(max_step)
    if not np.isfinite(step_limit) or step_limit <= 0.0:
        raise ValueError("max_step must be a positive finite value")

    generated: list[TaskState] = []
    start = state.arm_qpos
    current_state = state
    for index, waypoint in enumerate(waypoints):
        end = _finite_vector(
            waypoint,
            name=f"waypoints[{index}]",
            expected_size=state.arm_qpos.size,
        )
        largest_change = float(np.max(np.abs(end - start)))
        count = max(2, int(np.ceil(largest_change / step_limit)) + 1)
        for alpha in np.linspace(0.0, 1.0, count)[1:]:
            arm_qpos = (1.0 - alpha) * start + alpha * end
            current_state = current_state.with_updates(
                phase=phase,
                arm_qpos=arm_qpos,
            )
            generated.append(current_state)
        start = end
    return generated


def change_gripper(
    state: TaskState,
    *,
    target: float,
    steps: int = 17,
    phase: str = "change_gripper",
    active_target: str | None | object = _KEEP_TARGET,
) -> list[TaskState]:
    """Interpolate the gripper value while preserving all other state."""

    target_value = float(target)
    if not np.isfinite(target_value):
        raise ValueError("target must be finite")
    step_count = _positive_count(steps, name="steps", minimum=2)

    generated: list[TaskState] = []
    for alpha in np.linspace(0.0, 1.0, step_count)[1:]:
        gripper = (1.0 - alpha) * state.gripper + alpha * target_value
        updates = {
            "phase": phase,
            "gripper": gripper,
        }
        if active_target is not _KEEP_TARGET:
            updates["active_target"] = active_target
        generated.append(state.with_updates(**updates))
    return generated
