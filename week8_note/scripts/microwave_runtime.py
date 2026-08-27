"""Build an isolated Week8 runtime around the existing microwave asset."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from itertools import product
from pathlib import Path

import mujoco
import numpy as np

from week6_note.scripts import run_panda_reach_cabinet_handle as cab
from week7_note.scripts import run_level_5_sequential_open_both_doors as level5
from week7_note.task_system.mujoco_adapter import (
    MujocoJointMapping,
    MujocoStateAdapter,
)
from week7_note.task_system.panda_validation import PandaStateValidator


ROOT = Path(__file__).resolve().parents[1]
XML_DIR = ROOT / "xml"
TASK_XML = XML_DIR / "microwave_generalization.xml"
RAISED_PANDA_XML = XML_DIR / "franka_panda_raised_for_microwave.xml"
SOURCE_PANDA_XML = Path(
    "/home/users/dazhi.sun-labs/projects/week6_note/xml/"
    "franka_panda_shifted_for_cabinet.xml"
)
PANDA_LIFT_HEIGHT = 0.48

SOURCE_HANDLE_GEOM = "033_microwave_front_door_handle_bar"
MICROWAVE_DOOR_BODY = "microwave_door"
MICROWAVE_DOOR_JOINT = "body_to_front_door"
HANDLE_PROXY = "week8_microwave_handle_proxy"
DOOR_COLLISION_PROXY = "week8_microwave_door_collision_proxy"
ENTRY_DOOR_BODY = "entry_door"
ENTRY_DOOR_JOINT = "frame_to_door"
ENTRY_DOOR_PANEL_GEOM = "011_entry_door_door_door_panel"
ENTRY_HANDLE_PROXY = "week8_entry_door_handle_proxy"
ENTRY_DOOR_COLLISION_PROXY = "week8_entry_door_collision_proxy"
ENTRY_HANDLE_SUPPORTS = (
    "week8_entry_handle_support_lower",
    "week8_entry_handle_support_upper",
)


def _named_id(
    model: mujoco.MjModel,
    object_type: mujoco.mjtObj,
    name: str,
) -> int:
    object_id = mujoco.mj_name2id(model, object_type, name)
    if object_id < 0:
        raise ValueError(f"MuJoCo object {name!r} does not exist")
    return int(object_id)


def _geom_corners_in_body(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    geom_id: int,
    body_id: int,
) -> np.ndarray:
    geom_rotation = data.geom_xmat[geom_id].reshape(3, 3)
    local_center = model.geom_aabb[geom_id, :3]
    half_extent = model.geom_aabb[geom_id, 3:]
    world_center = data.geom_xpos[geom_id] + geom_rotation @ local_center
    body_rotation = data.xmat[body_id].reshape(3, 3)
    body_position = data.xpos[body_id]
    corners = []
    for signs in product((-1.0, 1.0), repeat=3):
        world_corner = world_center + geom_rotation @ (
            np.asarray(signs) * half_extent
        )
        corners.append(body_rotation.T @ (world_corner - body_position))
    return np.asarray(corners)


def _box_for_geoms(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_id: int,
    geom_ids: list[int],
    *,
    margin: tuple[float, float, float],
) -> tuple[np.ndarray, np.ndarray]:
    corners = np.concatenate(
        [
            _geom_corners_in_body(model, data, geom_id, body_id)
            for geom_id in geom_ids
        ],
        axis=0,
    )
    lower = np.min(corners, axis=0)
    upper = np.max(corners, axis=0)
    center = 0.5 * (lower + upper)
    half_extent = 0.5 * (upper - lower) + np.asarray(margin)
    return center, half_extent


def _numbers(values: np.ndarray) -> str:
    return " ".join(f"{float(value):.9f}" for value in values)


def _ensure_raised_panda_xml() -> None:
    if not SOURCE_PANDA_XML.is_file():
        raise FileNotFoundError(
            f"source Panda XML does not exist: {SOURCE_PANDA_XML}"
        )
    tree = ET.parse(SOURCE_PANDA_XML)
    root = tree.getroot()
    root.set("model", "week8_panda_with_vertical_lift")
    mobile_base = root.find(".//body[@name='mobile_panda_base']")
    if mobile_base is None:
        raise RuntimeError("mobile_panda_base is missing from Panda XML")
    link0 = mobile_base.find("./body[@name='link0']")
    if link0 is None:
        raise RuntimeError("link0 is missing from mobile Panda body")
    link0.set("pos", f"0 0 {PANDA_LIFT_HEIGHT:.9f}")

    lift_names = {
        "week8_vertical_lift_visual",
        "week8_vertical_lift_collision",
    }
    for geom in list(mobile_base.findall("geom")):
        if geom.get("name") in lift_names:
            mobile_base.remove(geom)
    lift_bottom = 0.13
    lift_center = 0.5 * (lift_bottom + PANDA_LIFT_HEIGHT)
    lift_half_height = 0.5 * (PANDA_LIFT_HEIGHT - lift_bottom)
    ET.SubElement(
        mobile_base,
        "geom",
        {
            "name": "week8_vertical_lift_visual",
            "type": "cylinder",
            "pos": f"0 0 {lift_center:.9f}",
            "size": f"0.075 {lift_half_height:.9f}",
            "rgba": "0.18 0.22 0.24 1",
            "contype": "0",
            "conaffinity": "0",
        },
    )
    ET.SubElement(
        mobile_base,
        "geom",
        {
            "name": "week8_vertical_lift_collision",
            "type": "cylinder",
            "pos": f"0 0 {lift_center:.9f}",
            "size": f"0.080 {lift_half_height:.9f}",
            "rgba": "0 0 0 0",
            "contype": "1",
            "conaffinity": "1",
            "group": "3",
        },
    )
    XML_DIR.mkdir(parents=True, exist_ok=True)
    tree.write(RAISED_PANDA_XML, encoding="utf-8", xml_declaration=True)


def ensure_week8_task_xml() -> dict:
    """Create a derived XML with reusable articulated-object proxies."""

    if not level5.TASK_XML.is_file():
        raise FileNotFoundError(
            f"stable Level5 XML does not exist: {level5.TASK_XML}"
        )

    source_model = mujoco.MjModel.from_xml_path(str(level5.TASK_XML))
    source_data = mujoco.MjData(source_model)
    mujoco.mj_forward(source_model, source_data)
    body_id = _named_id(
        source_model,
        mujoco.mjtObj.mjOBJ_BODY,
        MICROWAVE_DOOR_BODY,
    )
    handle_id = _named_id(
        source_model,
        mujoco.mjtObj.mjOBJ_GEOM,
        SOURCE_HANDLE_GEOM,
    )
    handle_center, handle_size = _box_for_geoms(
        source_model,
        source_data,
        body_id,
        [handle_id],
        margin=(0.002, 0.002, 0.002),
    )
    # The visual bar is thinner than the contact sleeve used by the accepted
    # cabinet grasps. Keep the proxy centered on the real mesh, but give it a
    # practical fingertip contact thickness without changing its appearance.
    handle_size = np.maximum(handle_size, np.array([0.024, 0.022, 0.090]))

    door_geom_ids = []
    for geom_id in range(source_model.ngeom):
        if int(source_model.geom_bodyid[geom_id]) != body_id:
            continue
        name = (
            mujoco.mj_id2name(
                source_model,
                mujoco.mjtObj.mjOBJ_GEOM,
                geom_id,
            )
            or ""
        )
        if "handle" not in name:
            door_geom_ids.append(geom_id)
    door_center, door_size = _box_for_geoms(
        source_model,
        source_data,
        body_id,
        door_geom_ids,
        margin=(0.002, 0.001, 0.002),
    )

    entry_body_id = _named_id(
        source_model,
        mujoco.mjtObj.mjOBJ_BODY,
        ENTRY_DOOR_BODY,
    )
    entry_panel_id = _named_id(
        source_model,
        mujoco.mjtObj.mjOBJ_GEOM,
        ENTRY_DOOR_PANEL_GEOM,
    )
    entry_panel_center, entry_panel_size = _box_for_geoms(
        source_model,
        source_data,
        entry_body_id,
        [entry_panel_id],
        margin=(0.002, 0.002, 0.002),
    )
    entry_panel_lower = entry_panel_center - entry_panel_size
    entry_panel_upper = entry_panel_center + entry_panel_size
    entry_handle_center = np.array(
        [
            entry_panel_upper[0] - 0.14,
            entry_panel_upper[1] + 0.075,
            entry_panel_lower[2] + 0.95,
        ],
        dtype=float,
    )
    entry_handle_size = np.array([0.022, 0.022, 0.12], dtype=float)

    _ensure_raised_panda_xml()
    tree = ET.parse(level5.TASK_XML)
    root = tree.getroot()
    root.set("model", "week8_microwave_generalization")
    include = root.find("include")
    if include is None:
        raise RuntimeError("Panda include is missing from source XML")
    include.set("file", str(RAISED_PANDA_XML.resolve()))
    door_body = root.find(f".//body[@name='{MICROWAVE_DOOR_BODY}']")
    if door_body is None:
        raise RuntimeError("microwave door body is missing from source XML")
    for geom in list(door_body.findall("geom")):
        if geom.get("name") in {HANDLE_PROXY, DOOR_COLLISION_PROXY}:
            door_body.remove(geom)

    ET.SubElement(
        door_body,
        "geom",
        {
            "name": HANDLE_PROXY,
            "type": "box",
            "pos": _numbers(handle_center),
            "size": _numbers(handle_size),
            "rgba": "0 0 0 0",
            "contype": "2",
            "conaffinity": "3",
        },
    )

    entry_body = root.find(f".//body[@name='{ENTRY_DOOR_BODY}']")
    if entry_body is None:
        raise RuntimeError("entry door body is missing from source XML")
    entry_proxy_names = {
        ENTRY_HANDLE_PROXY,
        ENTRY_DOOR_COLLISION_PROXY,
        *ENTRY_HANDLE_SUPPORTS,
    }
    for geom in list(entry_body.findall("geom")):
        if geom.get("name") in entry_proxy_names:
            entry_body.remove(geom)

    ET.SubElement(
        entry_body,
        "geom",
        {
            "name": ENTRY_HANDLE_PROXY,
            "type": "box",
            "pos": _numbers(entry_handle_center),
            "size": _numbers(entry_handle_size),
            "rgba": "0.72 0.70 0.62 1",
            "contype": "2",
            "conaffinity": "3",
        },
    )
    for name, z_offset in zip(ENTRY_HANDLE_SUPPORTS, (-0.085, 0.085)):
        support_center = entry_handle_center.copy()
        support_center[1] = 0.5 * entry_handle_center[1]
        support_center[2] += z_offset
        ET.SubElement(
            entry_body,
            "geom",
            {
                "name": name,
                "type": "box",
                "pos": _numbers(support_center),
                "size": "0.030 0.038 0.012",
                "rgba": "0.68 0.66 0.58 1",
                "contype": "0",
                "conaffinity": "0",
            },
        )
    ET.SubElement(
        entry_body,
        "geom",
        {
            "name": ENTRY_DOOR_COLLISION_PROXY,
            "type": "box",
            "pos": _numbers(entry_panel_center),
            "size": _numbers(entry_panel_size),
            "rgba": "0 0 0 0",
            "contype": "1",
            "conaffinity": "1",
        },
    )
    ET.SubElement(
        door_body,
        "geom",
        {
            "name": DOOR_COLLISION_PROXY,
            "type": "box",
            "pos": _numbers(door_center),
            "size": _numbers(door_size),
            "rgba": "0 0 0 0",
            "contype": "1",
            "conaffinity": "1",
        },
    )

    XML_DIR.mkdir(parents=True, exist_ok=True)
    tree.write(TASK_XML, encoding="utf-8", xml_declaration=True)
    return {
        "source_xml": str(level5.TASK_XML),
        "task_xml": str(TASK_XML),
        "raised_panda_xml": str(RAISED_PANDA_XML),
        "panda_lift_height": PANDA_LIFT_HEIGHT,
        "handle_proxy": HANDLE_PROXY,
        "handle_proxy_center": handle_center.tolist(),
        "handle_proxy_size": handle_size.tolist(),
        "door_collision_proxy": DOOR_COLLISION_PROXY,
        "door_collision_proxy_center": door_center.tolist(),
        "door_collision_proxy_size": door_size.tolist(),
        "entry_handle_proxy": ENTRY_HANDLE_PROXY,
        "entry_handle_proxy_center": entry_handle_center.tolist(),
        "entry_handle_proxy_size": entry_handle_size.tolist(),
        "entry_door_collision_proxy": ENTRY_DOOR_COLLISION_PROXY,
        "entry_door_collision_proxy_center": entry_panel_center.tolist(),
        "entry_door_collision_proxy_size": entry_panel_size.tolist(),
    }


def create_microwave_runtime(
    task_xml: str | Path | None = None,
) -> tuple[
    mujoco.MjModel,
    mujoco.MjData,
    MujocoStateAdapter,
    PandaStateValidator,
]:
    selected_xml = TASK_XML if task_xml is None else Path(task_xml).resolve()
    if selected_xml == TASK_XML.resolve():
        ensure_week8_task_xml()
    elif not selected_xml.is_file():
        raise FileNotFoundError(f"task XML does not exist: {selected_xml}")
    model = mujoco.MjModel.from_xml_path(str(selected_xml))
    data = mujoco.MjData(model)
    mapping = MujocoJointMapping(
        base_joints=("mobile_base_x", "mobile_base_y", "mobile_base_yaw"),
        arm_joints=tuple(f"joint{index}" for index in range(1, 8)),
        gripper_joints=("finger_joint1", "finger_joint2"),
        base_origin=(
            float(cab.MOBILE_BASE_START[0]),
            float(cab.MOBILE_BASE_START[1]),
            0.0,
        ),
        object_joint_aliases={
            "left_hinge": "left_hinge",
            "right_hinge": "right_hinge",
            "microwave_hinge": MICROWAVE_DOOR_JOINT,
            "entry_hinge": ENTRY_DOOR_JOINT,
        },
    )
    adapter = MujocoStateAdapter(model, data, mapping)
    validator = PandaStateValidator(
        adapter,
        allowed_finger_target_geoms={
            level5.LEFT_HANDLE,
            level5.RIGHT_HANDLE,
            SOURCE_HANDLE_GEOM,
            HANDLE_PROXY,
            ENTRY_HANDLE_PROXY,
        },
    )
    return model, data, adapter, validator
