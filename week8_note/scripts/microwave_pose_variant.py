"""Create an isolated translated and rotated microwave scene variant."""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np

from .microwave_runtime import (
    HANDLE_PROXY,
    TASK_XML,
    _box_for_geoms,
    ensure_week8_task_xml,
)
from .target_approach import target_relative_base_goal


ROOT = Path(__file__).resolve().parents[1]
MOVED_TASK_XML = ROOT / "xml" / "microwave_pose_shifted_rotated.xml"
SCENE_REPORT_PATH = (
    ROOT / "results" / "microwave_pose_shifted_rotated_scene.json"
)
BLOCKED_TASK_XML = (
    ROOT / "xml" / "microwave_pose_shifted_rotated_preferred_blocked.xml"
)
BLOCKED_SCENE_REPORT_PATH = (
    ROOT / "results" / "microwave_preferred_base_blocked_scene.json"
)
TRANSLATION = np.array([0.15, -0.05, 0.0], dtype=float)
YAW_DEGREES = 10.0
MICROWAVE_BODIES = {
    "microwave_door",
    "microwave_tray",
    "microwave_turntable",
    "microwave_upper_knob",
    "microwave_lower_knob",
}
PREFERRED_BASE_OFFSET = np.array([-0.32700001, -0.60800185], dtype=float)
BACKUP_BASE_OFFSET = np.array([0.0, -0.60], dtype=float)
BASE_YAW_OFFSET = 0.05


def _numbers(values: np.ndarray) -> str:
    return " ".join(f"{float(value):.9f}" for value in values)


def _microwave_center() -> np.ndarray:
    model = mujoco.MjModel.from_xml_path(str(TASK_XML))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    geom_ids = []
    for geom_id in range(model.ngeom):
        name = (
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
            or ""
        )
        body_id = int(model.geom_bodyid[geom_id])
        body_name = (
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id)
            or ""
        )
        if "microwave" in name and body_name == "static_room_shell":
            geom_ids.append(geom_id)
    if not geom_ids:
        raise RuntimeError("no static microwave shell geoms were found")
    body_id = int(model.geom_bodyid[geom_ids[0]])
    center, _ = _box_for_geoms(
        model,
        data,
        body_id,
        geom_ids,
        margin=(0.0, 0.0, 0.0),
    )
    return center


def ensure_moved_microwave_xml() -> dict:
    """Move every microwave component without modifying the source XML."""

    ensure_week8_task_xml()
    center = _microwave_center()
    yaw = math.radians(YAW_DEGREES)
    cosine = math.cos(yaw)
    sine = math.sin(yaw)
    rotation = np.array(
        [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )
    quaternion = np.array(
        [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)],
        dtype=float,
    )
    static_geom_translation = center + TRANSLATION - rotation @ center

    tree = ET.parse(TASK_XML)
    root = tree.getroot()
    root.set("model", "week8_microwave_pose_shifted_rotated")
    static_shell = root.find(".//body[@name='static_room_shell']")
    if static_shell is None:
        raise RuntimeError("static_room_shell is missing from source XML")

    moved_static_geoms = 0
    for geom in static_shell.findall("./geom"):
        if "microwave" not in geom.get("name", ""):
            continue
        geom.set("pos", _numbers(static_geom_translation))
        geom.set("quat", _numbers(quaternion))
        moved_static_geoms += 1

    moved_bodies = 0
    for body in root.findall(".//body"):
        if body.get("name") not in MICROWAVE_BODIES:
            continue
        if body.get("quat") is not None or body.get("euler") is not None:
            raise RuntimeError(
                f"microwave body {body.get('name')!r} already has a rotation"
            )
        old_position = np.fromstring(body.get("pos", ""), sep=" ")
        if old_position.shape != (3,):
            raise RuntimeError(
                f"microwave body {body.get('name')!r} has an invalid position"
            )
        new_position = center + rotation @ (old_position - center) + TRANSLATION
        body.set("pos", _numbers(new_position))
        body.set("quat", _numbers(quaternion))
        moved_bodies += 1

    if moved_static_geoms != 11 or moved_bodies != len(MICROWAVE_BODIES):
        raise RuntimeError(
            "microwave transform was incomplete: "
            f"static_geoms={moved_static_geoms}, bodies={moved_bodies}"
        )

    MOVED_TASK_XML.parent.mkdir(parents=True, exist_ok=True)
    tree.write(MOVED_TASK_XML, encoding="utf-8", xml_declaration=True)
    # Compile immediately so an invalid derived XML fails at creation time.
    mujoco.MjModel.from_xml_path(str(MOVED_TASK_XML))
    report = {
        "source_xml": str(TASK_XML),
        "moved_xml": str(MOVED_TASK_XML),
        "microwave_center": center.tolist(),
        "translation": TRANSLATION.tolist(),
        "yaw_degrees": YAW_DEGREES,
        "moved_static_geom_count": moved_static_geoms,
        "moved_body_count": moved_bodies,
    }
    SCENE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCENE_REPORT_PATH.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def ensure_preferred_base_blocked_xml() -> dict:
    """Add a static blocker at the preferred target-relative base goal."""

    moved_report = ensure_moved_microwave_xml()
    model = mujoco.MjModel.from_xml_path(str(MOVED_TASK_XML))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    handle_id = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        HANDLE_PROXY,
    )
    if handle_id < 0:
        raise RuntimeError(f"target geom {HANDLE_PROXY!r} is missing")
    preferred_goal = target_relative_base_goal(
        data.geom_xpos[handle_id],
        data.geom_xmat[handle_id].reshape(3, 3),
        base_offset=PREFERRED_BASE_OFFSET,
        yaw_offset=BASE_YAW_OFFSET,
        reference_yaw=0.0,
    )

    tree = ET.parse(MOVED_TASK_XML)
    root = tree.getroot()
    root.set("model", "week8_microwave_preferred_base_blocked")
    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("worldbody is missing from moved task XML")
    for geom in list(worldbody.findall("./geom")):
        if geom.get("name") == "week8_preferred_base_blocker":
            worldbody.remove(geom)
    ET.SubElement(
        worldbody,
        "geom",
        {
            "name": "week8_preferred_base_blocker",
            "type": "cylinder",
            "pos": (
                f"{preferred_goal[0]:.9f} {preferred_goal[1]:.9f} 0.240000000"
            ),
            "size": "0.110000000 0.240000000",
            "rgba": "0.72 0.18 0.12 1",
            "contype": "1",
            "conaffinity": "1",
        },
    )
    tree.write(BLOCKED_TASK_XML, encoding="utf-8", xml_declaration=True)
    mujoco.MjModel.from_xml_path(str(BLOCKED_TASK_XML))
    report = {
        "source_xml": str(MOVED_TASK_XML),
        "blocked_xml": str(BLOCKED_TASK_XML),
        "microwave_transform": moved_report,
        "preferred_base_goal": preferred_goal.tolist(),
        "preferred_base_offset": PREFERRED_BASE_OFFSET.tolist(),
        "backup_base_offset": BACKUP_BASE_OFFSET.tolist(),
        "blocker_radius": 0.11,
        "blocker_half_height": 0.24,
    }
    BLOCKED_SCENE_REPORT_PATH.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    print(json.dumps(ensure_moved_microwave_xml(), indent=2))
