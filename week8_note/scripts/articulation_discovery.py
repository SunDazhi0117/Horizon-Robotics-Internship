"""Discover the articulated joint that owns a target MuJoCo geom."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import mujoco


_JOINT_TYPE_NAMES = {
    int(mujoco.mjtJoint.mjJNT_FREE): "free",
    int(mujoco.mjtJoint.mjJNT_BALL): "ball",
    int(mujoco.mjtJoint.mjJNT_SLIDE): "slide",
    int(mujoco.mjtJoint.mjJNT_HINGE): "hinge",
}


def _object_name(
    model: mujoco.MjModel,
    object_type: mujoco.mjtObj,
    object_id: int,
) -> str:
    return (
        mujoco.mj_id2name(model, object_type, int(object_id))
        or f"unnamed_{int(object_id)}"
    )


def _named_id(
    model: mujoco.MjModel,
    object_type: mujoco.mjtObj,
    name: str,
) -> int:
    object_id = mujoco.mj_name2id(model, object_type, str(name))
    if object_id < 0:
        raise ValueError(f"MuJoCo object {name!r} does not exist")
    return int(object_id)


@dataclass(frozen=True, slots=True)
class ArticulationInfo:
    target_geom: str
    target_geom_id: int
    target_body: str
    target_body_id: int
    moving_body: str
    moving_body_id: int
    joint_name: str
    joint_id: int
    joint_type: str
    joint_axis_local: tuple[float, float, float]
    joint_axis_world: tuple[float, float, float]
    joint_limited: bool
    joint_range: tuple[float, float] | None
    qpos_address: int
    target_world_position: tuple[float, float, float]

    def to_dict(self) -> dict:
        return asdict(self)


def _body_joint_ids(model: mujoco.MjModel, body_id: int) -> list[int]:
    count = int(model.body_jntnum[body_id])
    if count == 0:
        return []
    start = int(model.body_jntadr[body_id])
    return list(range(start, start + count))


def discover_articulation(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    target_geom: str,
    *,
    joint_name: str | None = None,
) -> ArticulationInfo:
    """Find the nearest scalar joint controlling a target geom's body.

    The search begins at the geom's owning body and walks toward worldbody.
    This handles both a joint directly on the target body and a target nested
    below another articulated body.
    """

    mujoco.mj_forward(model, data)
    geom_id = _named_id(model, mujoco.mjtObj.mjOBJ_GEOM, target_geom)
    target_body_id = int(model.geom_bodyid[geom_id])

    requested_joint_id = None
    if joint_name is not None:
        requested_joint_id = _named_id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            joint_name,
        )

    body_id = target_body_id
    selected_joint_id = None
    selected_body_id = None
    while body_id != 0:
        scalar_joints = [
            candidate
            for candidate in _body_joint_ids(model, body_id)
            if int(model.jnt_type[candidate])
            in {
                int(mujoco.mjtJoint.mjJNT_HINGE),
                int(mujoco.mjtJoint.mjJNT_SLIDE),
            }
        ]
        if requested_joint_id is not None:
            scalar_joints = [
                candidate
                for candidate in scalar_joints
                if candidate == requested_joint_id
            ]
        if len(scalar_joints) == 1:
            selected_joint_id = scalar_joints[0]
            selected_body_id = body_id
            break
        if len(scalar_joints) > 1:
            names = [
                _object_name(model, mujoco.mjtObj.mjOBJ_JOINT, candidate)
                for candidate in scalar_joints
            ]
            raise ValueError(
                f"target geom {target_geom!r} is controlled by multiple "
                f"scalar joints on one body: {names}; provide joint_name"
            )
        body_id = int(model.body_parentid[body_id])

    if selected_joint_id is None or selected_body_id is None:
        detail = "" if joint_name is None else f" {joint_name!r}"
        raise ValueError(
            f"no controlling scalar joint{detail} found for "
            f"target geom {target_geom!r}"
        )

    joint_type_id = int(model.jnt_type[selected_joint_id])
    joint_type = _JOINT_TYPE_NAMES[joint_type_id]
    axis_local = model.jnt_axis[selected_joint_id].copy()
    body_rotation = data.xmat[selected_body_id].reshape(3, 3)
    axis_world = body_rotation @ axis_local
    limited = bool(model.jnt_limited[selected_joint_id])
    joint_range = None
    if limited:
        joint_range = tuple(
            float(value) for value in model.jnt_range[selected_joint_id]
        )

    return ArticulationInfo(
        target_geom=str(target_geom),
        target_geom_id=geom_id,
        target_body=_object_name(
            model,
            mujoco.mjtObj.mjOBJ_BODY,
            target_body_id,
        ),
        target_body_id=target_body_id,
        moving_body=_object_name(
            model,
            mujoco.mjtObj.mjOBJ_BODY,
            selected_body_id,
        ),
        moving_body_id=selected_body_id,
        joint_name=_object_name(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            selected_joint_id,
        ),
        joint_id=selected_joint_id,
        joint_type=joint_type,
        joint_axis_local=tuple(float(value) for value in axis_local),
        joint_axis_world=tuple(float(value) for value in axis_world),
        joint_limited=limited,
        joint_range=joint_range,
        qpos_address=int(model.jnt_qposadr[selected_joint_id]),
        target_world_position=tuple(
            float(value) for value in data.geom_xpos[geom_id]
        ),
    )
