"""Shared contact and visual-overlap checks for the Level 1-4 tasks."""

from __future__ import annotations

import mujoco
import numpy as np

from week6_note.scripts import run_panda_handle_pull_minimal as minimal


ALLOWED_HANDLE_BODIES = {"left_finger", "right_finger"}
PANDA_BODY_PREFIXES = ("link", "hand", "left_finger", "right_finger", "mobile_panda")
TARGET_GEOMS = (
    minimal.HANDLE_SLEEVE_GEOM,
    *minimal.HANDLE_SUPPORT_GEOMS,
    "009_double_door_cabinet_right_door_right_door_slab",
)


def body_name_for_geom(model: mujoco.MjModel, geom_id: int) -> str:
    body_id = int(model.geom_bodyid[geom_id])
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id) or ""


def geom_name(model: mujoco.MjModel, geom_id: int) -> str:
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or f"geom_{geom_id}"


def handle_contact_records(
    model: mujoco.MjModel,
    data: mujoco.MjData,
) -> tuple[list[dict], list[dict]]:
    handle_id = minimal.obj_id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        minimal.HANDLE_SLEEVE_GEOM,
    )
    finger_contacts: list[dict] = []
    forbidden_contacts: list[dict] = []

    for contact_index in range(data.ncon):
        contact = data.contact[contact_index]
        geom1 = int(contact.geom1)
        geom2 = int(contact.geom2)
        if handle_id not in {geom1, geom2}:
            continue

        other_geom = geom2 if geom1 == handle_id else geom1
        other_body = body_name_for_geom(model, other_geom)
        if not other_body.startswith(PANDA_BODY_PREFIXES):
            continue

        record = {
            "contact_index": int(contact_index),
            "other_geom": geom_name(model, other_geom),
            "other_body": other_body,
            "dist": float(contact.dist),
        }
        if other_body in ALLOWED_HANDLE_BODIES:
            finger_contacts.append(record)
        else:
            forbidden_contacts.append(record)

    return finger_contacts, forbidden_contacts


def contact_sample(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    phase: str,
    step_index: int,
) -> dict:
    handle_pos = minimal.geom_pos(model, data, minimal.HANDLE_SLEEVE_GEOM)
    gripper_pos = minimal.gripper_center(model, data)
    left_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")
    right_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")
    left_pos = data.xpos[left_id].copy()
    right_pos = data.xpos[right_id].copy()
    finger_delta = right_pos - left_pos
    finger_contacts, forbidden_contacts = handle_contact_records(model, data)

    return {
        "phase": phase,
        "step_index": step_index,
        "gripper_to_handle_distance": float(np.linalg.norm(gripper_pos - handle_pos)),
        "finger_xy_separation": float(np.linalg.norm(finger_delta[:2])),
        "finger_z_separation": float(abs(finger_delta[2])),
        "finger_contact_bodies": sorted(
            {item["other_body"] for item in finger_contacts}
        ),
        "finger_contact_count": len(finger_contacts),
        "forbidden_contact_count": len(forbidden_contacts),
        "min_forbidden_contact_dist": min(
            (item["dist"] for item in forbidden_contacts),
            default=None,
        ),
        "forbidden_contacts": forbidden_contacts,
    }


def geom_obb(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    geom_id: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    local_center = model.geom_aabb[geom_id, :3].copy()
    half_extent = model.geom_aabb[geom_id, 3:].copy()
    rotation = data.geom_xmat[geom_id].reshape(3, 3).copy()
    center = data.geom_xpos[geom_id].copy() + rotation @ local_center
    return center, rotation, half_extent


def obb_overlap(
    center_a: np.ndarray,
    rotation_a: np.ndarray,
    extent_a: np.ndarray,
    center_b: np.ndarray,
    rotation_b: np.ndarray,
    extent_b: np.ndarray,
    eps: float = 1e-8,
) -> tuple[bool, float]:
    r = rotation_a.T @ rotation_b
    abs_r = np.abs(r) + eps
    t = rotation_a.T @ (center_b - center_a)
    min_margin = float("inf")

    for i in range(3):
        radius_a = extent_a[i]
        radius_b = float(np.dot(extent_b, abs_r[i, :]))
        margin = radius_a + radius_b - abs(t[i])
        if margin < 0.0:
            return False, float(margin)
        min_margin = min(min_margin, float(margin))

    for j in range(3):
        radius_a = float(np.dot(extent_a, abs_r[:, j]))
        radius_b = extent_b[j]
        margin = radius_a + radius_b - abs(float(np.dot(t, r[:, j])))
        if margin < 0.0:
            return False, float(margin)
        min_margin = min(min_margin, float(margin))

    for i in range(3):
        for j in range(3):
            radius_a = (
                extent_a[(i + 1) % 3] * abs_r[(i + 2) % 3, j]
                + extent_a[(i + 2) % 3] * abs_r[(i + 1) % 3, j]
            )
            radius_b = (
                extent_b[(j + 1) % 3] * abs_r[i, (j + 2) % 3]
                + extent_b[(j + 2) % 3] * abs_r[i, (j + 1) % 3]
            )
            value = abs(
                t[(i + 2) % 3] * r[(i + 1) % 3, j]
                - t[(i + 1) % 3] * r[(i + 2) % 3, j]
            )
            margin = float(radius_a + radius_b - value)
            if margin < 0.0:
                return False, margin
            min_margin = min(min_margin, margin)

    return True, min_margin


def panda_geom_ids(model: mujoco.MjModel) -> list[int]:
    return [
        geom_id
        for geom_id in range(model.ngeom)
        if body_name_for_geom(model, geom_id).startswith(PANDA_BODY_PREFIXES)
    ]


def target_geom_ids(model: mujoco.MjModel) -> list[int]:
    return [
        minimal.obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
        for name in TARGET_GEOMS
    ]


def visual_overlap_sample(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    phase: str,
    step_index: int,
    panda_ids: list[int],
    target_ids: list[int],
    allowed_finger_target_geoms: set[str] | None = None,
) -> dict:
    allowed_finger_targets = (
        {minimal.HANDLE_SLEEVE_GEOM}
        if allowed_finger_target_geoms is None
        else allowed_finger_target_geoms
    )
    overlaps = []
    target_obbs = {
        target_id: geom_obb(model, data, target_id)
        for target_id in target_ids
    }

    for panda_id in panda_ids:
        panda_body = body_name_for_geom(model, panda_id)
        panda_obb = geom_obb(model, data, panda_id)
        for target_id, target_obb in target_obbs.items():
            target_name = geom_name(model, target_id)
            if (
                panda_body in ALLOWED_HANDLE_BODIES
                and target_name in allowed_finger_targets
            ):
                continue
            overlap, margin = obb_overlap(*panda_obb, *target_obb)
            if overlap:
                overlaps.append(
                    {
                        "phase": phase,
                        "step_index": step_index,
                        "panda_geom": geom_name(model, panda_id),
                        "panda_body": panda_body,
                        "target_geom": target_name,
                        "overlap_margin": margin,
                        "panda_contype": int(model.geom_contype[panda_id]),
                        "target_contype": int(model.geom_contype[target_id]),
                    }
                )

    return {
        "phase": phase,
        "step_index": step_index,
        "visual_overlap_count": len(overlaps),
        "visual_overlaps": overlaps,
    }
