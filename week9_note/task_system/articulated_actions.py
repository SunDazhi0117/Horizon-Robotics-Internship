"""Manipulation actions shared by the Week9 and Week10 scenes."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from week7_note.task_system.primitives import smooth_progress
from week7_note.task_system.state import TaskState
from week8_note.scripts.target_approach import TargetApproachActions


class ArticulatedObjectActions(TargetApproachActions):
    """Add grasp-preserving motion for scalar prismatic joints."""

    def action_registry(self) -> dict[str, object]:
        actions = super().action_registry()
        actions["follow_slide_joint"] = self.follow_slide_joint
        return actions

    def follow_slide_joint(
        self,
        state: TaskState,
        *,
        joint_name: str,
        moving_body: str,
        target_position: float,
        samples: int = 45,
        base_target: Sequence[float] | None = None,
        max_joint_step: float = 0.15,
        minimum_each_finger_contacts: int = 2,
        ik_position_tolerance: float = 0.004,
        ik_rotation_tolerance: float = 0.015,
        ik_continuity_weight: float = 0.003,
        ik_max_nfev: int = 1200,
        phase: str = "follow_slide_joint",
    ) -> list[TaskState]:
        """Move a slide joint while preserving the body-to-hand transform."""

        if joint_name not in state.object_joints:
            raise ValueError(
                f"object joint {joint_name!r} is missing from TaskState"
            )
        sample_count = int(samples)
        if sample_count < 2:
            raise ValueError("samples must be at least 2")
        step_limit = float(max_joint_step)
        if not np.isfinite(step_limit) or step_limit <= 0.0:
            raise ValueError("max_joint_step must be positive and finite")

        if base_target is None:
            end_base = state.base.copy()
        else:
            end_base = np.asarray(base_target, dtype=float)
            if end_base.shape != (3,) or not np.all(np.isfinite(end_base)):
                raise ValueError("base_target must contain three finite values")

        self.adapter.apply(state)
        body_pos, body_rot = self._body_pose(moving_body)
        hand_pos, hand_rot = self._body_pose(self.end_effector_body)
        body_to_hand_pos = body_rot.T @ (hand_pos - body_pos)
        body_to_hand_rot = body_rot.T @ hand_rot

        start_position = float(state.object_joints[joint_name])
        end_position = float(target_position)
        previous = state
        generated: list[TaskState] = []
        for sample_index, raw_alpha in enumerate(
            np.linspace(0.0, 1.0, sample_count)[1:],
            start=1,
        ):
            alpha = smooth_progress(float(raw_alpha))
            position = (
                (1.0 - alpha) * start_position + alpha * end_position
            )
            base = (1.0 - alpha) * state.base + alpha * end_base
            joints = dict(previous.object_joints)
            joints[joint_name] = float(position)
            candidate = previous.with_updates(
                phase=phase,
                base=base,
                object_joints=joints,
            )

            self.adapter.apply(candidate)
            body_pos, body_rot = self._body_pose(moving_body)
            desired_pos = body_pos + body_rot @ body_to_hand_pos
            desired_rot = body_rot @ body_to_hand_rot
            try:
                solved = self._solve_arm_pose(
                    candidate,
                    desired_pos,
                    desired_rot,
                    position_tolerance=ik_position_tolerance,
                    rotation_tolerance=ik_rotation_tolerance,
                    continuity_weight=ik_continuity_weight,
                    max_nfev=ik_max_nfev,
                )
            except ValueError as error:
                raise ValueError(
                    f"{error} at slide sample "
                    f"{sample_index}/{sample_count - 1} "
                    f"(position={position:.9f})"
                ) from error
            measured_step = float(np.max(np.abs(solved - previous.arm_qpos)))
            if measured_step > step_limit:
                raise ValueError(
                    f"arm joint step {measured_step:.9f} exceeds "
                    f"{step_limit} radians at slide sample "
                    f"{sample_index}/{sample_count - 1} "
                    f"(position={position:.9f})"
                )
            current = candidate.with_updates(arm_qpos=solved)
            generated.append(current)
            previous = current

        self._validate_states(
            generated,
            previous_state=state,
            minimum_each_finger_contacts=minimum_each_finger_contacts,
        )
        return generated
