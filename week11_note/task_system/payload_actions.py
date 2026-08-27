"""Grasp-preserving payload transport for Week11 transfer tasks."""

from __future__ import annotations

from collections.abc import Sequence

import mujoco
import numpy as np

from week7_note.task_system.primitives import smooth_progress
from week7_note.task_system.state import TaskState
from week9_note.task_system import ArticulatedObjectActions


class PayloadTransferActions(ArticulatedObjectActions):
    """Add lift-translate-lower transport to articulated-object actions."""

    def action_registry(self) -> dict[str, object]:
        actions = super().action_registry()
        actions["carry_payload"] = self.carry_payload
        return actions

    def _site_pose(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        site_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_SITE,
            str(name),
        )
        if site_id < 0:
            raise ValueError(f"MuJoCo site {name!r} does not exist")
        return (
            self.data.site_xpos[site_id].copy(),
            self.data.site_xmat[site_id].reshape(3, 3).copy(),
        )

    def _payload_joint_system(
        self,
        state_joint_names: Sequence[str],
    ) -> tuple[np.ndarray, tuple[str, str, str]]:
        names = tuple(str(name).strip() for name in state_joint_names)
        if len(names) != 3 or any(not name for name in names):
            raise ValueError("payload_joint_names must contain x, y, and z names")
        axes: list[np.ndarray] = []
        for state_name in names:
            if state_name not in self.adapter.mapping.object_joint_aliases:
                raise ValueError(
                    f"payload joint alias {state_name!r} is not configured"
                )
            model_name = self.adapter.mapping.object_joint_aliases[state_name]
            joint_id = mujoco.mj_name2id(
                self.model,
                mujoco.mjtObj.mjOBJ_JOINT,
                model_name,
            )
            if joint_id < 0 or int(self.model.jnt_type[joint_id]) != int(
                mujoco.mjtJoint.mjJNT_SLIDE
            ):
                raise ValueError(
                    f"payload joint {model_name!r} must be a slide joint"
                )
            axes.append(self.data.xaxis[joint_id].copy())
        axis_matrix = np.column_stack(axes)
        if abs(float(np.linalg.det(axis_matrix))) < 0.99:
            raise ValueError("payload slide axes must form a 3-D basis")
        return axis_matrix, names

    def carry_payload(
        self,
        state: TaskState,
        *,
        payload_body: str,
        payload_joint_names: Sequence[str],
        destination_site: str,
        base_target: Sequence[float],
        carry_height: float,
        destination_offset: Sequence[float] = (0.0, 0.0, 0.0),
        clearance_offset: Sequence[float] = (0.0, 0.0, 0.0),
        lift_samples: int = 25,
        clearance_samples: int = 31,
        translate_samples: int = 65,
        lower_samples: int = 25,
        max_joint_step: float = 0.15,
        minimum_each_finger_contacts: int = 2,
        ik_position_tolerance: float = 0.006,
        ik_rotation_tolerance: float = 0.02,
        ik_continuity_weight: float = 0.004,
        ik_max_nfev: int = 1500,
        phase: str = "carry_payload",
    ) -> list[TaskState]:
        """Lift a grasped item, carry it with the base, and lower it."""

        if state.active_target is None:
            raise ValueError("carry_payload requires an active grasp target")
        for name in payload_joint_names:
            if str(name) not in state.object_joints:
                raise ValueError(
                    f"payload joint {name!r} is missing from TaskState"
                )
        clearance = np.asarray(clearance_offset, dtype=float)
        if clearance.shape != (3,) or not np.all(np.isfinite(clearance)):
            raise ValueError("clearance_offset must contain three finite values")
        sample_counts = (
            int(lift_samples),
            int(clearance_samples),
            int(translate_samples),
            int(clearance_samples),
            int(lower_samples),
        )
        if any(count < 2 for count in sample_counts):
            raise ValueError("all carry segment sample counts must be at least 2")

        end_base = np.asarray(base_target, dtype=float)
        if end_base.shape != (3,) or not np.all(np.isfinite(end_base)):
            raise ValueError("base_target must contain three finite values")
        offset = np.asarray(destination_offset, dtype=float)
        if offset.shape != (3,) or not np.all(np.isfinite(offset)):
            raise ValueError("destination_offset must contain three finite values")
        height = float(carry_height)
        if not np.isfinite(height):
            raise ValueError("carry_height must be finite")

        self.adapter.apply(state)
        axis_matrix, joint_names = self._payload_joint_system(
            payload_joint_names
        )
        payload_start, payload_rotation = self._body_pose(payload_body)
        if not np.allclose(payload_rotation, np.eye(3), atol=1e-5):
            raise ValueError("payload body must start world-axis aligned")
        hand_start, hand_rotation = self._body_pose(self.end_effector_body)
        hand_to_payload = hand_rotation.T @ (payload_start - hand_start)
        site_position, site_rotation = self._site_pose(destination_site)
        payload_goal = site_position + site_rotation @ offset
        transit_z = max(height, float(payload_start[2]), float(payload_goal[2]))

        lifted_start = np.array(
            [payload_start[0], payload_start[1], transit_z]
        )
        lifted_goal = np.array([payload_goal[0], payload_goal[1], transit_z])
        base_clearance = np.array(
            [clearance[0], clearance[1], 0.0],
            dtype=float,
        )
        payload_points = (
            payload_start,
            lifted_start,
            lifted_start + clearance,
            lifted_goal + clearance,
            lifted_goal,
            payload_goal,
        )
        base_points = (
            state.base,
            state.base,
            state.base + base_clearance,
            end_base + base_clearance,
            end_base,
            end_base,
        )
        start_joint_values = np.array(
            [float(state.object_joints[name]) for name in joint_names],
            dtype=float,
        )

        previous = state
        generated: list[TaskState] = []
        for segment_index, sample_count in enumerate(sample_counts):
            start_payload = payload_points[segment_index]
            end_payload = payload_points[segment_index + 1]
            start_base = base_points[segment_index]
            segment_end_base = base_points[segment_index + 1]
            for sample_index, raw_alpha in enumerate(
                np.linspace(0.0, 1.0, sample_count)[1:],
                start=1,
            ):
                alpha = smooth_progress(float(raw_alpha))
                payload_position = (
                    (1.0 - alpha) * start_payload + alpha * end_payload
                )
                base = (
                    (1.0 - alpha) * start_base
                    + alpha * segment_end_base
                )
                joint_delta = np.linalg.solve(
                    axis_matrix,
                    payload_position - payload_start,
                )
                joints = dict(previous.object_joints)
                for name, value in zip(
                    joint_names,
                    start_joint_values + joint_delta,
                ):
                    joints[name] = float(value)
                candidate = previous.with_updates(
                    phase=phase,
                    base=base,
                    object_joints=joints,
                )
                desired_hand_position = (
                    payload_position - hand_rotation @ hand_to_payload
                )
                try:
                    solved = self._solve_arm_pose(
                        candidate,
                        desired_hand_position,
                        hand_rotation,
                        position_tolerance=ik_position_tolerance,
                        rotation_tolerance=ik_rotation_tolerance,
                        continuity_weight=ik_continuity_weight,
                        max_nfev=ik_max_nfev,
                    )
                except ValueError as error:
                    raise ValueError(
                        f"{error} during carry segment {segment_index + 1} "
                        f"sample {sample_index}/{sample_count - 1}"
                    ) from error
                measured_step = float(
                    np.max(np.abs(solved - previous.arm_qpos))
                )
                if measured_step > float(max_joint_step):
                    raise ValueError(
                        f"arm joint step {measured_step:.9f} exceeds "
                        f"{float(max_joint_step):.9f} during carry segment "
                        f"{segment_index + 1} sample {sample_index}"
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
