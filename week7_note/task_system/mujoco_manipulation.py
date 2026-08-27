"""Reusable MuJoCo grasp and articulated-joint actions."""

from __future__ import annotations

from collections.abc import Sequence

import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from .mujoco_adapter import MujocoStateAdapter
from .panda_validation import PandaStateValidator
from .primitives import change_gripper, move_arm, smooth_progress
from .state import TaskState


def planar_hinge_orbit_base(
    base: Sequence[float],
    hinge_anchor_xy: Sequence[float],
    signed_angle: float,
) -> np.ndarray:
    """Rotate a planar robot base pose around a vertical hinge anchor."""

    pose = np.asarray(base, dtype=float)
    anchor = np.asarray(hinge_anchor_xy, dtype=float)
    angle = float(signed_angle)
    if pose.shape != (3,) or not np.all(np.isfinite(pose)):
        raise ValueError("base must contain three finite values")
    if anchor.shape != (2,) or not np.all(np.isfinite(anchor)):
        raise ValueError("hinge_anchor_xy must contain two finite values")
    if not np.isfinite(angle):
        raise ValueError("signed_angle must be finite")

    cosine = float(np.cos(angle))
    sine = float(np.sin(angle))
    offset = pose[:2] - anchor
    return np.array(
        [
            anchor[0] + cosine * offset[0] - sine * offset[1],
            anchor[1] + sine * offset[0] + cosine * offset[1],
            pose[2] + angle,
        ],
        dtype=float,
    )


class MujocoManipulationActions:
    """Bind reusable manipulation actions to one MuJoCo runtime.

    The methods have the same ``handler(state, **parameters)`` shape used by
    TaskExecutor. Scene-specific names and target values are parameters rather
    than constants embedded in a Level script.
    """

    def __init__(
        self,
        adapter: MujocoStateAdapter,
        validator: PandaStateValidator | None = None,
        *,
        end_effector_body: str = "hand",
    ) -> None:
        self.adapter = adapter
        self.model = adapter.model
        self.data = adapter.data
        self.validator = validator
        self.end_effector_body = str(end_effector_body).strip()
        if not self.end_effector_body:
            raise ValueError("end_effector_body must be non-empty")
        self._body_id(self.end_effector_body)
        self._lower, self._upper = self._arm_joint_bounds()

    def action_registry(self) -> dict[str, object]:
        """Return runtime-bound handlers for TaskExecutor."""

        return {
            "grasp_target": self.grasp_target,
            "follow_hinge_joint": self.follow_hinge_joint,
        }

    def _body_id(self, name: str) -> int:
        body_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY,
            str(name),
        )
        if body_id < 0:
            raise ValueError(f"MuJoCo body {name!r} does not exist")
        return int(body_id)

    def _geom_id(self, name: str) -> int:
        geom_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_GEOM,
            str(name),
        )
        if geom_id < 0:
            raise ValueError(f"MuJoCo geom {name!r} does not exist")
        return int(geom_id)

    def _body_pose(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        body_id = self._body_id(name)
        return (
            self.data.xpos[body_id].copy(),
            self.data.xmat[body_id].reshape(3, 3).copy(),
        )

    def _geom_pose(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        geom_id = self._geom_id(name)
        return (
            self.data.geom_xpos[geom_id].copy(),
            self.data.geom_xmat[geom_id].reshape(3, 3).copy(),
        )

    def _arm_joint_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        lower: list[float] = []
        upper: list[float] = []
        for name in self.adapter.mapping.arm_joints:
            joint_id = mujoco.mj_name2id(
                self.model,
                mujoco.mjtObj.mjOBJ_JOINT,
                name,
            )
            if joint_id < 0:
                raise ValueError(f"MuJoCo joint {name!r} does not exist")
            if not bool(self.model.jnt_limited[joint_id]):
                raise ValueError(
                    f"arm joint {name!r} needs finite limits for IK"
                )
            lower.append(float(self.model.jnt_range[joint_id, 0]) + 1e-4)
            upper.append(float(self.model.jnt_range[joint_id, 1]) - 1e-4)
        return np.asarray(lower), np.asarray(upper)

    @staticmethod
    def _rotation_matrix(
        value: Sequence[Sequence[float]] | Sequence[float],
        *,
        name: str,
    ) -> np.ndarray:
        matrix = np.asarray(value, dtype=float)
        if matrix.size != 9:
            raise ValueError(f"{name} must contain nine values")
        matrix = matrix.reshape(3, 3)
        if not np.all(np.isfinite(matrix)):
            raise ValueError(f"{name} must contain finite values")
        if not np.allclose(matrix.T @ matrix, np.eye(3), atol=1e-5):
            raise ValueError(f"{name} must be an orthonormal rotation matrix")
        return matrix

    def target_hand_transform(
        self,
        state: TaskState,
        target_geom: str,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Capture the hand pose in a target geom's local frame."""

        self.adapter.apply(state)
        target_pos, target_rot = self._geom_pose(target_geom)
        hand_pos, hand_rot = self._body_pose(self.end_effector_body)
        return (
            target_rot.T @ (hand_pos - target_pos),
            target_rot.T @ hand_rot,
        )

    def _solve_arm_pose(
        self,
        state: TaskState,
        desired_pos: np.ndarray,
        desired_rot: np.ndarray,
        *,
        position_weight: float = 100.0,
        rotation_weight: float = 30.0,
        continuity_weight: float = 0.006,
        continuity_scale: float = 0.55,
        max_nfev: int = 900,
        position_tolerance: float = 0.002,
        rotation_tolerance: float = 0.01,
    ) -> np.ndarray:
        seed = state.arm_qpos.copy()

        def residual(qpos: np.ndarray) -> np.ndarray:
            self.adapter.apply(state.with_updates(arm_qpos=qpos))
            hand_pos, hand_rot = self._body_pose(self.end_effector_body)
            position_error = hand_pos - desired_pos
            rotation_error = Rotation.from_matrix(
                desired_rot.T @ hand_rot
            ).as_rotvec()
            continuity = (qpos - seed) / float(continuity_scale)
            return np.concatenate(
                (
                    position_error * float(position_weight),
                    rotation_error * float(rotation_weight),
                    continuity * float(continuity_weight),
                )
            )

        result = least_squares(
            residual,
            np.clip(seed, self._lower, self._upper),
            bounds=(self._lower, self._upper),
            xtol=1e-11,
            ftol=1e-11,
            gtol=1e-11,
            max_nfev=int(max_nfev),
        )
        solved = np.asarray(result.x, dtype=float)
        self.adapter.apply(state.with_updates(arm_qpos=solved))
        hand_pos, hand_rot = self._body_pose(self.end_effector_body)
        position_error = float(np.linalg.norm(hand_pos - desired_pos))
        rotation_error = float(
            np.linalg.norm(
                Rotation.from_matrix(desired_rot.T @ hand_rot).as_rotvec()
            )
        )
        if (
            not result.success
            or position_error > float(position_tolerance)
            or rotation_error > float(rotation_tolerance)
        ):
            raise ValueError(
                "IK failed: "
                f"success={result.success}, "
                f"position_error={position_error:.6f}, "
                f"rotation_error={rotation_error:.6f}"
            )
        return solved

    def _validate_states(
        self,
        states: Sequence[TaskState],
        *,
        previous_state: TaskState,
        minimum_final_finger_contacts: int = 0,
        minimum_each_finger_contacts: int = 0,
    ) -> None:
        if self.validator is None:
            if minimum_final_finger_contacts or minimum_each_finger_contacts:
                raise ValueError("finger-contact checks require a validator")
            return

        samples: list[dict] = []
        previous = previous_state
        for index, state in enumerate(states):
            sample = self.validator.validate(
                state,
                step_index=index,
                previous_state=previous,
            )
            if sample["environment_visual_overlap_count"]:
                raise ValueError(
                    f"visual overlap detected in phase {state.phase!r} "
                    f"at generated state {index}"
                )
            if sample["forbidden_active_target_contact_count"]:
                raise ValueError(
                    f"forbidden target contact detected in phase "
                    f"{state.phase!r} at generated state {index}"
                )
            if (
                minimum_each_finger_contacts
                and sample["active_target_unique_finger_contact_count"]
                < minimum_each_finger_contacts
            ):
                raise ValueError(
                    f"grasp lost in phase {state.phase!r} "
                    f"at generated state {index}"
                )
            samples.append(sample)
            previous = state

        if (
            samples
            and samples[-1]["active_target_unique_finger_contact_count"]
            < minimum_final_finger_contacts
        ):
            raise ValueError(
                "final grasp does not have the required finger contacts"
            )

    def grasp_target(
        self,
        state: TaskState,
        *,
        target_geom: str,
        closed_gripper: float,
        hand_offset: Sequence[float] | None = None,
        hand_rotation: Sequence[Sequence[float]] | Sequence[float] | None = None,
        capture_current_transform: bool = False,
        max_step: float = 0.045,
        close_steps: int = 17,
        minimum_final_finger_contacts: int = 2,
        phase: str = "grasp_target",
    ) -> list[TaskState]:
        """Move to a target-relative hand pose, then close the gripper."""

        target_geom = str(target_geom).strip()
        if not target_geom:
            raise ValueError("target_geom must be non-empty")
        self._geom_id(target_geom)

        if capture_current_transform:
            if hand_offset is not None or hand_rotation is not None:
                raise ValueError(
                    "capture_current_transform cannot be combined with an "
                    "explicit hand transform"
                )
            local_offset, local_rotation = self.target_hand_transform(
                state,
                target_geom,
            )
        else:
            if hand_offset is None or hand_rotation is None:
                raise ValueError(
                    "hand_offset and hand_rotation are required unless "
                    "capture_current_transform is true"
                )
            local_offset = np.asarray(hand_offset, dtype=float)
            if local_offset.shape != (3,) or not np.all(
                np.isfinite(local_offset)
            ):
                raise ValueError("hand_offset must contain three finite values")
            local_rotation = self._rotation_matrix(
                hand_rotation,
                name="hand_rotation",
            )

        target_state = state.with_updates(active_target=target_geom)
        self.adapter.apply(target_state)
        target_pos, target_rot = self._geom_pose(target_geom)
        desired_pos = target_pos + target_rot @ local_offset
        desired_rot = target_rot @ local_rotation
        solved = self._solve_arm_pose(
            target_state,
            desired_pos,
            desired_rot,
        )

        approach = move_arm(
            target_state,
            waypoints=[solved],
            max_step=max_step,
            phase=phase,
        )
        close = change_gripper(
            approach[-1],
            target=closed_gripper,
            steps=close_steps,
            phase=phase,
            active_target=target_geom,
        )
        generated = [*approach, *close]
        self._validate_states(
            generated,
            previous_state=state,
            minimum_final_finger_contacts=minimum_final_finger_contacts,
        )
        return generated

    def follow_hinge_joint(
        self,
        state: TaskState,
        *,
        joint_name: str,
        moving_body: str,
        target_angle: float,
        samples: int = 65,
        base_target: Sequence[float] | None = None,
        orbit_base_with_hinge: bool = False,
        max_joint_step: float = 0.15,
        minimum_each_finger_contacts: int = 2,
        ik_position_tolerance: float = 0.002,
        ik_rotation_tolerance: float = 0.01,
        ik_continuity_weight: float = 0.006,
        ik_max_nfev: int = 900,
        phase: str = "follow_hinge_joint",
    ) -> list[TaskState]:
        """Follow a moving body while one hinge moves to a target angle."""

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

        orbit_base = bool(orbit_base_with_hinge)
        if orbit_base and base_target is not None:
            raise ValueError(
                "base_target and orbit_base_with_hinge cannot be combined"
            )
        if base_target is None:
            end_base = state.base.copy()
        else:
            end_base = np.asarray(base_target, dtype=float)
            if end_base.shape != (3,) or not np.all(np.isfinite(end_base)):
                raise ValueError("base_target must contain three finite values")

        self.adapter.apply(state)
        hinge_anchor = None
        hinge_axis_sign = 1.0
        if orbit_base:
            model_joint_name = self.adapter.mapping.object_joint_aliases.get(
                joint_name,
                joint_name,
            )
            joint_id = mujoco.mj_name2id(
                self.model,
                mujoco.mjtObj.mjOBJ_JOINT,
                model_joint_name,
            )
            if joint_id < 0:
                raise ValueError(
                    f"MuJoCo joint {model_joint_name!r} does not exist"
                )
            if int(self.model.jnt_type[joint_id]) != int(
                mujoco.mjtJoint.mjJNT_HINGE
            ):
                raise ValueError(
                    "orbit_base_with_hinge requires a hinge joint"
                )
            hinge_axis = self.data.xaxis[joint_id].copy()
            if abs(float(hinge_axis[2])) < 0.99:
                raise ValueError(
                    "orbit_base_with_hinge requires a near-vertical "
                    "world-space hinge axis"
                )
            hinge_anchor = self.data.xanchor[joint_id, :2].copy()
            hinge_axis_sign = float(np.sign(hinge_axis[2]))
        body_pos, body_rot = self._body_pose(moving_body)
        hand_pos, hand_rot = self._body_pose(self.end_effector_body)
        body_to_hand_pos = body_rot.T @ (hand_pos - body_pos)
        body_to_hand_rot = body_rot.T @ hand_rot

        start_angle = float(state.object_joints[joint_name])
        end_angle = float(target_angle)
        previous = state
        generated: list[TaskState] = []
        for sample_index, raw_alpha in enumerate(
            np.linspace(0.0, 1.0, sample_count)[1:],
            start=1,
        ):
            alpha = smooth_progress(float(raw_alpha))
            angle = (1.0 - alpha) * start_angle + alpha * end_angle
            if orbit_base:
                signed_delta = hinge_axis_sign * (angle - start_angle)
                base = planar_hinge_orbit_base(
                    state.base,
                    hinge_anchor,
                    signed_delta,
                )
            else:
                base = (1.0 - alpha) * state.base + alpha * end_base
            joints = dict(previous.object_joints)
            joints[joint_name] = float(angle)
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
                    f"{error} at hinge sample "
                    f"{sample_index}/{sample_count - 1} "
                    f"(angle={angle:.9f})"
                ) from error
            measured_step = float(
                np.max(np.abs(solved - previous.arm_qpos))
            )
            if measured_step > step_limit:
                raise ValueError(
                    f"arm joint step {measured_step:.9f} exceeds "
                    f"{step_limit} radians at hinge sample "
                    f"{sample_index}/{sample_count - 1} "
                    f"(angle={angle:.9f})"
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
