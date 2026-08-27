"""Construct a shared MuJoCo runtime for Week9/Week10 task scenes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import mujoco

from week6_note.scripts import run_panda_reach_cabinet_handle as cabinet
from week7_note.task_system.mujoco_adapter import (
    MujocoJointMapping,
    MujocoStateAdapter,
)
from week7_note.task_system.panda_validation import PandaStateValidator


def _names(values: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ValueError(f"runtime.{field} must be a sequence")
    names = tuple(str(value).strip() for value in values)
    if not names or any(not name for name in names):
        raise ValueError(f"runtime.{field} must contain non-empty names")
    return names


def create_scenario_runtime(
    task_xml: str | Path,
    runtime_config: Mapping[str, object],
) -> tuple[
    mujoco.MjModel,
    mujoco.MjData,
    MujocoStateAdapter,
    PandaStateValidator,
]:
    """Load one task XML and bind its configured object-joint aliases."""

    selected_xml = Path(task_xml).expanduser().resolve()
    if not selected_xml.is_file():
        raise FileNotFoundError(f"task XML does not exist: {selected_xml}")
    aliases_raw = runtime_config.get("object_joint_aliases")
    if not isinstance(aliases_raw, Mapping) or not aliases_raw:
        raise ValueError("runtime.object_joint_aliases must be a mapping")
    aliases = {
        str(state_name).strip(): str(model_name).strip()
        for state_name, model_name in aliases_raw.items()
    }
    if any(not state_name or not model_name for state_name, model_name in aliases.items()):
        raise ValueError("runtime object-joint aliases must be non-empty")

    allowed_targets = _names(
        runtime_config.get("allowed_finger_target_geoms"),
        field="allowed_finger_target_geoms",
    )
    model = mujoco.MjModel.from_xml_path(str(selected_xml))
    data = mujoco.MjData(model)
    mapping = MujocoJointMapping(
        base_joints=("mobile_base_x", "mobile_base_y", "mobile_base_yaw"),
        arm_joints=tuple(f"joint{index}" for index in range(1, 8)),
        gripper_joints=("finger_joint1", "finger_joint2"),
        base_origin=(
            float(cabinet.MOBILE_BASE_START[0]),
            float(cabinet.MOBILE_BASE_START[1]),
            0.0,
        ),
        object_joint_aliases=aliases,
    )
    adapter = MujocoStateAdapter(model, data, mapping)
    validator = PandaStateValidator(
        adapter,
        allowed_finger_target_geoms=allowed_targets,
    )
    return model, data, adapter, validator
