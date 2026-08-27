"""Apply reusable TaskState objects to a MuJoCo model."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

import mujoco
import numpy as np

from .state import TaskState


@dataclass(frozen=True, slots=True)
class MujocoJointMapping:
    """Map TaskState fields to scalar MuJoCo joints."""

    base_joints: tuple[str, str, str]
    arm_joints: tuple[str, ...]
    gripper_joints: tuple[str, ...]
    base_origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    object_joint_aliases: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.base_joints) != 3:
            raise ValueError("base_joints must contain x, y, and yaw joints")
        if not self.arm_joints:
            raise ValueError("arm_joints cannot be empty")
        if not self.gripper_joints:
            raise ValueError("gripper_joints cannot be empty")
        if len(self.base_origin) != 3:
            raise ValueError("base_origin must contain x, y, and yaw")

        all_names = (
            *self.base_joints,
            *self.arm_joints,
            *self.gripper_joints,
        )
        if any(not str(name).strip() for name in all_names):
            raise ValueError("joint names must be non-empty")
        if len(set(all_names)) != len(all_names):
            raise ValueError("base, arm, and gripper joints must be unique")

        origin = tuple(float(value) for value in self.base_origin)
        if not np.all(np.isfinite(origin)):
            raise ValueError("base_origin must contain finite values")

        aliases: dict[str, str] = {}
        for raw_state_name, raw_model_name in self.object_joint_aliases.items():
            state_name = str(raw_state_name).strip()
            model_name = str(raw_model_name).strip()
            if not state_name or not model_name:
                raise ValueError("object joint aliases must be non-empty")
            aliases[state_name] = model_name

        object.__setattr__(self, "base_origin", origin)
        object.__setattr__(
            self,
            "object_joint_aliases",
            MappingProxyType(aliases),
        )


class MujocoStateAdapter:
    """Write TaskState values into MjData and read them back."""

    def __init__(
        self,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        mapping: MujocoJointMapping,
    ) -> None:
        self.model = model
        self.data = data
        self.mapping = mapping
        self._qpos_addresses: dict[str, int] = {}

        required_names = (
            *mapping.base_joints,
            *mapping.arm_joints,
            *mapping.gripper_joints,
            *mapping.object_joint_aliases.values(),
        )
        for name in required_names:
            self._qpos_address(name)

    def _qpos_address(self, joint_name: str) -> int:
        name = str(joint_name)
        cached = self._qpos_addresses.get(name)
        if cached is not None:
            return cached

        joint_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_JOINT,
            name,
        )
        if joint_id < 0:
            raise ValueError(f"MuJoCo joint {name!r} does not exist")

        joint_type = int(self.model.jnt_type[joint_id])
        unsupported = {
            int(mujoco.mjtJoint.mjJNT_FREE),
            int(mujoco.mjtJoint.mjJNT_BALL),
        }
        if joint_type in unsupported:
            raise ValueError(
                f"MuJoCo joint {name!r} is not a scalar hinge or slide joint"
            )

        address = int(self.model.jnt_qposadr[joint_id])
        self._qpos_addresses[name] = address
        return address

    def _model_joint_name(self, state_joint_name: str) -> str:
        return self.mapping.object_joint_aliases.get(
            state_joint_name,
            state_joint_name,
        )

    def _set_joint(self, name: str, value: float) -> None:
        numeric_value = float(value)
        if not np.isfinite(numeric_value):
            raise ValueError(f"joint {name!r} value must be finite")
        self.data.qpos[self._qpos_address(name)] = numeric_value

    def _read_joint(self, name: str) -> float:
        return float(self.data.qpos[self._qpos_address(name)])

    def apply(self, state: TaskState) -> None:
        """Apply one command state and recompute MuJoCo kinematics."""

        if state.arm_qpos.size != len(self.mapping.arm_joints):
            raise ValueError(
                "TaskState arm_qpos size does not match arm joint mapping"
            )

        for index, joint_name in enumerate(self.mapping.base_joints):
            relative_value = state.base[index] - self.mapping.base_origin[index]
            self._set_joint(joint_name, relative_value)

        for joint_name, value in zip(
            self.mapping.arm_joints,
            state.arm_qpos,
        ):
            self._set_joint(joint_name, float(value))

        for joint_name in self.mapping.gripper_joints:
            self._set_joint(joint_name, state.gripper)

        for state_name, value in state.object_joints.items():
            self._set_joint(self._model_joint_name(state_name), value)

        self.data.qvel[:] = 0.0
        mujoco.mj_forward(self.model, self.data)

    def read_base(self) -> np.ndarray:
        """Read absolute [x, y, yaw] using the configured base origin."""

        return np.array(
            [
                self._read_joint(joint_name) + self.mapping.base_origin[index]
                for index, joint_name in enumerate(self.mapping.base_joints)
            ],
            dtype=float,
        )

    def read_arm_qpos(self) -> np.ndarray:
        return np.array(
            [self._read_joint(name) for name in self.mapping.arm_joints],
            dtype=float,
        )

    def read_gripper(self) -> float:
        values = np.array(
            [self._read_joint(name) for name in self.mapping.gripper_joints],
            dtype=float,
        )
        return float(np.mean(values))

    def read_object_joints(
        self,
        state_joint_names: tuple[str, ...] | list[str],
    ) -> dict[str, float]:
        return {
            state_name: self._read_joint(
                self._model_joint_name(state_name)
            )
            for state_name in state_joint_names
        }

    def read_state(self, template: TaskState) -> TaskState:
        """Read the fields represented by a template TaskState."""

        return TaskState(
            phase=template.phase,
            base=self.read_base(),
            arm_qpos=self.read_arm_qpos(),
            gripper=self.read_gripper(),
            object_joints=self.read_object_joints(
                list(template.object_joints)
            ),
            active_target=template.active_target,
        )
