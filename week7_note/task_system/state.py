"""Task state shared by reusable motion primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

import numpy as np


_KEEP_TARGET = object()


def _readonly_vector(
    value: np.ndarray | list[float] | tuple[float, ...],
    *,
    name: str,
    expected_size: int | None = None,
) -> np.ndarray:
    vector = np.asarray(value, dtype=float).copy()
    if vector.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional vector")
    if expected_size is not None and vector.size != expected_size:
        raise ValueError(f"{name} must contain exactly {expected_size} values")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values")
    vector.setflags(write=False)
    return vector


@dataclass(frozen=True, slots=True)
class TaskState:
    """One commanded state in a scripted manipulation task.

    Arrays and object-joint values are copied during construction. A primitive
    therefore creates new states instead of mutating states that are already in
    the trajectory.
    """

    phase: str
    base: np.ndarray
    arm_qpos: np.ndarray
    gripper: float
    object_joints: Mapping[str, float] = field(default_factory=dict)
    active_target: str | None = None

    def __post_init__(self) -> None:
        phase = str(self.phase).strip()
        if not phase:
            raise ValueError("phase must be a non-empty string")

        base = _readonly_vector(self.base, name="base", expected_size=3)
        arm_qpos = _readonly_vector(self.arm_qpos, name="arm_qpos")
        if arm_qpos.size == 0:
            raise ValueError("arm_qpos must contain at least one joint value")

        gripper = float(self.gripper)
        if not np.isfinite(gripper):
            raise ValueError("gripper must be finite")

        joints: dict[str, float] = {}
        for raw_name, raw_value in self.object_joints.items():
            name = str(raw_name).strip()
            if not name:
                raise ValueError("object joint names must be non-empty")
            value = float(raw_value)
            if not np.isfinite(value):
                raise ValueError(f"object joint {name!r} must be finite")
            joints[name] = value

        target = self.active_target
        if target is not None:
            target = str(target).strip()
            if not target:
                raise ValueError("active_target must be non-empty or None")

        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "base", base)
        object.__setattr__(self, "arm_qpos", arm_qpos)
        object.__setattr__(self, "gripper", gripper)
        object.__setattr__(
            self,
            "object_joints",
            MappingProxyType(joints),
        )
        object.__setattr__(self, "active_target", target)

    def with_updates(
        self,
        *,
        phase: str | None = None,
        base: np.ndarray | list[float] | tuple[float, ...] | None = None,
        arm_qpos: np.ndarray | list[float] | tuple[float, ...] | None = None,
        gripper: float | None = None,
        object_joints: Mapping[str, float] | None = None,
        active_target: str | None | object = _KEEP_TARGET,
    ) -> TaskState:
        """Create a new state while preserving fields that are not supplied."""

        target = (
            self.active_target
            if active_target is _KEEP_TARGET
            else active_target
        )
        return TaskState(
            phase=self.phase if phase is None else phase,
            base=self.base if base is None else base,
            arm_qpos=self.arm_qpos if arm_qpos is None else arm_qpos,
            gripper=self.gripper if gripper is None else gripper,
            object_joints=(
                self.object_joints
                if object_joints is None
                else object_joints
            ),
            active_target=target,
        )

    def with_object_joint(
        self,
        name: str,
        value: float,
        *,
        phase: str | None = None,
    ) -> TaskState:
        """Create a state with one object-joint value replaced."""

        joints = dict(self.object_joints)
        joints[name] = value
        return self.with_updates(phase=phase, object_joints=joints)

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""

        return {
            "phase": self.phase,
            "base": self.base.tolist(),
            "arm_qpos": self.arm_qpos.tolist(),
            "gripper": self.gripper,
            "object_joints": dict(self.object_joints),
            "active_target": self.active_target,
        }
