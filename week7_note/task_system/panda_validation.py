"""TaskState validation for the mobile Panda used in Week6 and Week7."""

from __future__ import annotations

from collections.abc import Iterable

import mujoco
import numpy as np

from week6_note.scripts import run_panda_handle_pull_minimal as minimal
from week7_note.scripts import level_validation_helpers as validation

from .mujoco_adapter import MujocoStateAdapter
from .state import TaskState


class PandaStateValidator:
    """Validate Panda overlap, target contact, and command continuity."""

    def __init__(
        self,
        adapter: MujocoStateAdapter,
        *,
        allowed_finger_target_geoms: Iterable[str] = (),
        excluded_environment_geoms: Iterable[str] = (
            "reference_ground",
            "000_Mesh_0",
        ),
    ) -> None:
        self.adapter = adapter
        self.model = adapter.model
        self.data = adapter.data
        self.allowed_finger_target_geoms = {
            str(name)
            for name in allowed_finger_target_geoms
        }
        excluded = {str(name) for name in excluded_environment_geoms}

        self.panda_geom_ids = validation.panda_geom_ids(self.model)
        panda_ids = set(self.panda_geom_ids)
        self.environment_geom_ids = [
            geom_id
            for geom_id in range(self.model.ngeom)
            if geom_id not in panda_ids
            and validation.geom_name(self.model, geom_id) not in excluded
        ]

    def _target_contacts(
        self,
        target_name: str,
    ) -> tuple[set[str], list[dict]]:
        target_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_GEOM,
            target_name,
        )
        if target_id < 0:
            raise ValueError(f"target geom {target_name!r} does not exist")

        finger_bodies: set[str] = set()
        forbidden: list[dict] = []
        for contact_index in range(self.data.ncon):
            contact = self.data.contact[contact_index]
            geom1 = int(contact.geom1)
            geom2 = int(contact.geom2)
            if target_id not in {geom1, geom2}:
                continue

            other_id = geom2 if geom1 == target_id else geom1
            other_body = validation.body_name_for_geom(
                self.model,
                other_id,
            )
            if not other_body.startswith(validation.PANDA_BODY_PREFIXES):
                continue

            record = {
                "other_geom": validation.geom_name(
                    self.model,
                    other_id,
                ),
                "other_body": other_body,
                "distance": float(contact.dist),
            }
            if other_body in validation.ALLOWED_HANDLE_BODIES:
                finger_bodies.add(other_body)
            else:
                forbidden.append(record)
        return finger_bodies, forbidden

    def validate(
        self,
        state: TaskState,
        *,
        step_index: int,
        previous_state: TaskState | None = None,
    ) -> dict:
        """Apply and validate one TaskState."""

        self.adapter.apply(state)
        overlap = validation.visual_overlap_sample(
            self.model,
            self.data,
            state.phase,
            step_index,
            self.panda_geom_ids,
            self.environment_geom_ids,
            allowed_finger_target_geoms=self.allowed_finger_target_geoms,
        )

        contact_bodies: set[str] = set()
        forbidden_contacts: list[dict] = []
        target_distance = None
        if state.active_target is not None:
            contact_bodies, forbidden_contacts = self._target_contacts(
                state.active_target
            )
            target_id = mujoco.mj_name2id(
                self.model,
                mujoco.mjtObj.mjOBJ_GEOM,
                state.active_target,
            )
            target_distance = float(
                np.linalg.norm(
                    minimal.gripper_center(self.model, self.data)
                    - self.data.geom_xpos[target_id]
                )
            )

        actual = self.adapter.read_state(state)
        return {
            "phase": state.phase,
            "step_index": int(step_index),
            "commanded_base": state.base.tolist(),
            "base": actual.base.tolist(),
            "base_command_error": float(
                np.linalg.norm(actual.base - state.base)
            ),
            "commanded_arm_qpos": state.arm_qpos.tolist(),
            "arm_qpos": actual.arm_qpos.tolist(),
            "gripper": actual.gripper,
            "commanded_object_joints": dict(state.object_joints),
            "object_joints": dict(actual.object_joints),
            "active_target": state.active_target,
            "gripper_to_active_target_distance": target_distance,
            "active_target_finger_contacts": sorted(contact_bodies),
            "active_target_unique_finger_contact_count": len(
                contact_bodies
            ),
            "forbidden_active_target_contacts": forbidden_contacts,
            "forbidden_active_target_contact_count": len(
                forbidden_contacts
            ),
            "environment_visual_overlap_count": overlap[
                "visual_overlap_count"
            ],
            "environment_visual_overlaps": overlap["visual_overlaps"],
            "max_joint_step_from_previous": (
                0.0
                if previous_state is None
                else float(
                    np.max(
                        np.abs(
                            state.arm_qpos - previous_state.arm_qpos
                        )
                    )
                )
            ),
        }
