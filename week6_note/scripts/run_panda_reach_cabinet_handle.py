#!/usr/bin/env python3
"""Use Franka Panda to reach the cabinet handle in the generated room."""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ROOM_XML = ROOT / "xml" / "articulated_demo_with_actuators.xml"
PANDA_SRC_XML = ROOT / "assets" / "franka_panda" / "panda.xml"
PANDA_SHIFTED_XML = ROOT / "xml" / "franka_panda_shifted_for_cabinet.xml"
TASK_XML = ROOT / "xml" / "articulated_demo_room_with_panda_reach.xml"
OUTPUT_DIR = ROOT / "outputs"
IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

RIGHT_HANDLE_GEOM = "010_double_door_cabinet_right_door_right_handle"
RIGHT_HANDLE_GRASP_PROXY_GEOM = "right_cabinet_handle_grasp_proxy"
RIGHT_HINGE_JOINT = "right_hinge"
MOBILE_BASE_START = np.array([3.62, 2.28, 0.0])
MOBILE_BASE_GOAL = np.array([4.2247, 2.5323, 0.0682])
PANDA_BASE_POS = "0 0 0"
PANDA_BASE_QUAT = "0.7071068 0 0 0.7071068"
PANDA_HOME = np.array([0.0, -0.55, 0.0, -2.25, 0.0, 1.75, 0.78])
PANDA_REACH = np.array([2.6501, -0.4850, 2.1944, -0.9377, 0.1553, 1.8856, -1.9659])
GRIPPER_OPEN_CTRL = 255.0
GRIPPER_PREGRASP_CTRL = 180.0
GRIPPER_GRASP_CTRL = 200.0
SUCCESS_DISTANCE = 0.09
DOOR_FACE_MIN_X = 4.885
HANDLE_STANDOFF_TARGET = np.array([4.835, 2.872, 0.70])
FINGER_OPEN_START = 0.04
FINGER_OPEN_FINAL = 0.022
ARM_STAGE_ORDER = [0, 1, 2, 4, 6, 3, 5]
RIGHT_CABINET_PULL_ANGLE = 0.50
RIGHT_CABINET_OPEN_ANGLE = 1.57079632679
PANDA_PULL_OPEN = np.array([2.8838, -0.0447, 2.2841, -1.1402, 0.0987, 1.0835, -1.8242])
PANDA_FOLLOW_90_WAYPOINTS = np.array([
    [0.500000, 4.226248, 2.529589, 0.069936, 2.885532, -0.046807, 2.285592, -1.138835, 0.095450, 1.087564, -1.824162],
    [0.562988, 4.203271, 2.520919, 0.063535, 2.884976, -0.046166, 2.280447, -1.138713, 0.088233, 1.086499, -1.826877],
    [0.625976, 4.174257, 2.508602, 0.043483, 2.889356, -0.043007, 2.271827, -1.151845, 0.090496, 1.122485, -1.830306],
    [0.688964, 4.188184, 2.495811, 0.224212, 2.897293, 0.085589, 2.245104, -1.253187, 0.011808, 1.090196, -1.754374],
    [0.751952, 4.159711, 2.473556, 0.171562, 2.895657, 0.071308, 2.283456, -1.231643, -0.035534, 1.143102, -1.757182],
    [0.814940, 4.216643, 2.422465, 0.424010, 2.897298, 0.193468, 2.276910, -1.301699, -0.042907, 1.077255, -1.810534],
    [0.877928, 4.189610, 2.406008, 0.416941, 2.889549, 0.212686, 2.271802, -1.320606, -0.076221, 1.114027, -1.842991],
    [0.940916, 4.097712, 2.486774, 0.425556, 2.881405, 0.398216, 2.136400, -1.355682, -0.131747, 1.245852, -1.837437],
    [1.003904, 4.135679, 2.435608, 0.445055, 2.888871, 0.484802, 2.264825, -1.457824, -0.150169, 1.225374, -1.854419],
    [1.066892, 4.105808, 2.342008, 0.450000, 2.897300, 0.315147, 2.238292, -1.430512, -0.176932, 1.393042, -1.855722],
    [1.129880, 4.092663, 2.300000, 0.450000, 2.897300, 0.252743, 2.227833, -1.412721, -0.192245, 1.456076, -1.857380],
    [1.192868, 4.041086, 2.301960, 0.422787, 2.870087, 0.206348, 2.174035, -1.396799, -0.218442, 1.526254, -1.859167],
    [1.255856, 4.003479, 2.318964, 0.404268, 2.850208, 0.214272, 2.134441, -1.394802, -0.221976, 1.540345, -1.884228],
    [1.318844, 4.039430, 2.367549, 0.331979, 2.725652, 0.278341, 2.470928, -1.440038, -0.695139, 1.214834, -1.830533],
    [1.381832, 4.036837, 2.359742, 0.360818, 2.656172, 0.420438, 2.529753, -1.625852, -0.827832, 1.293619, -1.872157],
    [1.444820, 4.016976, 2.395278, 0.327874, 2.670185, 0.461576, 2.483648, -1.657041, -0.946822, 1.219857, -1.895515],
    [1.465000, 4.019307, 2.403403, 0.339158, 2.673718, 0.492417, 2.474378, -1.626741, -0.920271, 1.218022, -1.922451],
    [1.474618, 4.020300, 2.360116, 0.524649, 2.717482, 0.722256, 2.345947, -1.633641, -0.614127, 1.422401, -1.829148],
    [1.484236, 4.061909, 2.374638, 0.491743, 2.653617, 0.834288, 2.471421, -1.753860, -0.610146, 1.445350, -1.954478],
    [1.493854, 4.078619, 2.390677, 0.487506, 2.659164, 0.916380, 2.501272, -1.781579, -0.637773, 1.383568, -2.032520],
    [1.503471, 4.078723, 2.378074, 0.442745, 2.668808, 0.951411, 2.493595, -1.837579, -0.566922, 1.522251, -2.121495],
    [1.513089, 4.079937, 2.372684, 0.391276, 2.685879, 0.980363, 2.488485, -1.889696, -0.510332, 1.642359, -2.235129],
    [1.522707, 4.092636, 2.375099, 0.385429, 2.691176, 0.971699, 2.500524, -1.860851, -0.492871, 1.536772, -2.282304],
    [1.532325, 4.083595, 2.351118, 0.435301, 2.696875, 0.923666, 2.454738, -1.816173, -0.433125, 1.528432, -2.353846],
    [1.541943, 4.096284, 2.340044, 0.466796, 2.721656, 0.961328, 2.465894, -1.815796, -0.444612, 1.501546, -2.446017],
    [1.551561, 4.136876, 2.351746, 0.402379, 2.664462, 0.937058, 2.559749, -1.837717, -0.417387, 1.372536, -2.533414],
    [1.561178, 4.067976, 2.417703, 0.522050, 2.657542, 0.928766, 2.355447, -1.592824, -0.394932, 1.275460, -2.571387],
    [1.570796, 4.124369, 2.413697, 0.312886, 2.622879, 0.712865, 2.301172, -1.539232, 0.040850, 1.030658, -2.697341],
])
COLLISION_PROXY_NAMES = [
    "right_cabinet_door_collision_proxy",
    "right_cabinet_handle_collision_proxy",
]
CABINET_COLLISION_GEOMS = [
    "009_double_door_cabinet_right_door_right_door_slab",
    "010_double_door_cabinet_right_door_right_handle",
]


def ensure_panda_shifted_xml() -> None:
    tree = ET.parse(PANDA_SRC_XML)
    root = tree.getroot()

    compiler = root.find("compiler")
    if compiler is not None:
        root.remove(compiler)

    option = root.find("option")
    if option is not None:
        root.remove(option)

    keyframe = root.find("keyframe")
    if keyframe is not None:
        root.remove(keyframe)

    asset = root.find("asset")
    if asset is None:
        raise RuntimeError("Panda XML missing asset section")
    for mesh in asset.findall("mesh"):
        file_name = mesh.get("file")
        if file_name:
            mesh.set("file", str(PANDA_SRC_XML.parent / "assets" / file_name))

    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("Panda XML missing worldbody")
    for light in list(worldbody.findall("light")):
        worldbody.remove(light)

    link0 = worldbody.find("./body[@name='link0']")
    if link0 is None:
        raise RuntimeError("Panda XML missing link0 body")
    link0.set("pos", PANDA_BASE_POS)
    link0.set("quat", PANDA_BASE_QUAT)

    for finger_body_name in ["left_finger", "right_finger"]:
        finger_body = link0.find(f".//body[@name='{finger_body_name}']")
        if finger_body is not None:
            for geom in finger_body.findall("geom"):
                if geom.get("class") == "visual":
                    continue
                geom.set("contype", "3")
                geom.set("conaffinity", "3")

    worldbody.remove(link0)

    mobile_base = ET.Element(
        "body",
        {
            "name": "mobile_panda_base",
            "pos": " ".join(f"{v:.6f}" for v in MOBILE_BASE_START),
        },
    )
    ET.SubElement(
        mobile_base,
        "joint",
        {
            "name": "mobile_base_x",
            "type": "slide",
            "axis": "1 0 0",
            "range": "-10 10",
            "damping": "80",
        },
    )
    ET.SubElement(
        mobile_base,
        "joint",
        {
            "name": "mobile_base_y",
            "type": "slide",
            "axis": "0 1 0",
            "range": "-10 10",
            "damping": "80",
        },
    )
    ET.SubElement(
        mobile_base,
        "joint",
        {
            "name": "mobile_base_yaw",
            "type": "hinge",
            "axis": "0 0 1",
            "range": "-3.14159 3.14159",
            "damping": "20",
        },
    )
    ET.SubElement(
        mobile_base,
        "geom",
        {
            "name": "mobile_panda_base_visual",
            "type": "cylinder",
            "pos": "0 0 0.070",
            "size": "0.180 0.035",
            "rgba": "0.12 0.16 0.18 1",
            "contype": "0",
            "conaffinity": "0",
        },
    )
    ET.SubElement(
        mobile_base,
        "geom",
        {
            "name": "mobile_panda_base_top_plate",
            "type": "cylinder",
            "pos": "0 0 0.120",
            "size": "0.135 0.014",
            "rgba": "0.22 0.25 0.27 1",
            "contype": "0",
            "conaffinity": "0",
        },
    )
    ET.SubElement(
        mobile_base,
        "geom",
        {
            "name": "mobile_panda_unicycle_wheel",
            "type": "cylinder",
            "pos": "0 0 0.042",
            "quat": "0.7071068 0.7071068 0 0",
            "size": "0.090 0.055",
            "rgba": "0.015 0.017 0.020 1",
            "contype": "0",
            "conaffinity": "0",
        },
    )
    for pad_name, y_pos in [
        ("mobile_panda_balance_pad_left", 0.155),
        ("mobile_panda_balance_pad_right", -0.155),
    ]:
        ET.SubElement(
            mobile_base,
            "geom",
            {
                "name": pad_name,
                "type": "sphere",
                "pos": f"0 {y_pos:.3f} 0.022",
                "size": "0.030",
                "rgba": "0.035 0.040 0.045 1",
                "contype": "0",
                "conaffinity": "0",
            },
        )
    mobile_base.append(link0)
    worldbody.append(mobile_base)

    actuator = root.find("actuator")
    if actuator is None:
        actuator = ET.SubElement(root, "actuator")
    for name in ["mobile_base_x_actuator", "mobile_base_y_actuator", "mobile_base_yaw_actuator"]:
        old = actuator.find(f"./position[@name='{name}']")
        if old is not None:
            actuator.remove(old)
    actuator.insert(
        0,
        ET.Element(
            "position",
            {
                "name": "mobile_base_yaw_actuator",
                "joint": "mobile_base_yaw",
                "kp": "600",
                "ctrlrange": "-3.14159 3.14159",
                "forcerange": "-500 500",
            },
        ),
    )
    actuator.insert(
        0,
        ET.Element(
            "position",
            {
                "name": "mobile_base_y_actuator",
                "joint": "mobile_base_y",
                "kp": "900",
                "ctrlrange": "-10 10",
                "forcerange": "-800 800",
            },
        ),
    )
    actuator.insert(
        0,
        ET.Element(
            "position",
            {
                "name": "mobile_base_x_actuator",
                "joint": "mobile_base_x",
                "kp": "900",
                "ctrlrange": "-10 10",
                "forcerange": "-800 800",
            },
        ),
    )

    PANDA_SHIFTED_XML.parent.mkdir(parents=True, exist_ok=True)
    tree.write(PANDA_SHIFTED_XML, encoding="utf-8", xml_declaration=True)


def ensure_task_xml() -> None:
    ensure_panda_shifted_xml()
    tree = ET.parse(ROOM_XML)
    root = tree.getroot()
    root.set("model", "articulated_demo_room_with_panda_reach")

    old_includes = root.findall("include")
    for include in old_includes:
        root.remove(include)
    root.insert(1, ET.Element("include", {"file": str(PANDA_SHIFTED_XML)}))

    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("Room XML missing worldbody")
    for body in root.iter("body"):
        for geom in list(body.findall("geom")):
            if geom.get("name") in [
                "panda_handle_target_marker",
                "panda_base_marker",
                *COLLISION_PROXY_NAMES,
                RIGHT_HANDLE_GRASP_PROXY_GEOM,
            ]:
                body.remove(geom)
    for geom in list(worldbody.findall("geom")):
        if geom.get("name") in [
            "panda_handle_target_marker",
            "panda_base_marker",
            *COLLISION_PROXY_NAMES,
            RIGHT_HANDLE_GRASP_PROXY_GEOM,
        ]:
            worldbody.remove(geom)

    for geom in root.iter("geom"):
        if geom.get("name") in CABINET_COLLISION_GEOMS:
            geom.set("contype", "1")
            geom.set("conaffinity", "1")

    right_door_body = worldbody.find("./body[@name='cabinet_right_door']")
    if right_door_body is None:
        raise RuntimeError("Room XML missing cabinet_right_door body")
    right_door_body.append(
        ET.Element(
            "geom",
            {
                "name": RIGHT_HANDLE_GRASP_PROXY_GEOM,
                "type": "box",
                "pos": "-0.048 0.382 0.600",
                "size": "0.075 0.060 0.095",
                "rgba": "0 1 0 0",
                "contype": "2",
                "conaffinity": "2",
            },
        )
    )

    TASK_XML.parent.mkdir(parents=True, exist_ok=True)
    tree.write(TASK_XML, encoding="utf-8", xml_declaration=True)


def obj_id(model: mujoco.MjModel, obj_type: mujoco.mjtObj, name: str) -> int:
    idx = mujoco.mj_name2id(model, obj_type, name)
    if idx < 0:
        raise KeyError(name)
    return idx


def render(model: mujoco.MjModel, data: mujoco.MjData, view: str) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if view == "top":
        camera.lookat[:] = [4.55, 2.82, 0.55]
        camera.distance = 1.85
        camera.azimuth = 0.0
        camera.elevation = -88.0
    else:
        camera.lookat[:] = [4.65, 2.82, 0.75]
        camera.distance = 1.55
        camera.azimuth = -55.0
        camera.elevation = -28.0
    with mujoco.Renderer(model, width=760, height=570) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def save(path: Path, pixels: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)


def cabinet_contact_stats(model: mujoco.MjModel, data: mujoco.MjData) -> tuple[int, float | None]:
    cabinet_ids = set()
    for name in [*COLLISION_PROXY_NAMES, *CABINET_COLLISION_GEOMS]:
        geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
        if geom_id >= 0:
            cabinet_ids.add(geom_id)
    count = 0
    min_dist: float | None = None
    for contact_index in range(data.ncon):
        contact = data.contact[contact_index]
        if int(contact.geom1) in cabinet_ids or int(contact.geom2) in cabinet_ids:
            count += 1
            dist = float(contact.dist)
            min_dist = dist if min_dist is None else min(min_dist, dist)
    return count, min_dist


def handle_contact_stats(model: mujoco.MjModel, data: mujoco.MjData, handle_id: int) -> dict[str, object]:
    finger_contact_count = 0
    hand_count = 0
    min_dist: float | None = None
    bodies: list[str] = []
    finger_bodies: set[str] = set()
    for contact_index in range(data.ncon):
        contact = data.contact[contact_index]
        geom1 = int(contact.geom1)
        geom2 = int(contact.geom2)
        if geom1 != handle_id and geom2 != handle_id:
            continue
        other_geom = geom2 if geom1 == handle_id else geom1
        other_body_id = int(model.geom_bodyid[other_geom])
        other_body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, other_body_id)
        if other_body:
            bodies.append(other_body)
        if other_body in {"left_finger", "right_finger"}:
            finger_contact_count += 1
            finger_bodies.add(other_body)
        if other_body in {"hand", "link6", "link7"}:
            hand_count += 1
        dist = float(contact.dist)
        min_dist = dist if min_dist is None else min(min_dist, dist)
    return {
        "finger_count": finger_contact_count,
        "unique_finger_count": len(finger_bodies),
        "finger_bodies": sorted(finger_bodies),
        "hand_count": hand_count,
        "min_dist": min_dist,
        "bodies": bodies,
    }


def set_panda_qpos(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    qpos: np.ndarray,
    finger_opening: float = 0.035,
) -> None:
    for joint_index, value in enumerate(qpos, start=1):
        joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, f"joint{joint_index}")
        data.qpos[int(model.jnt_qposadr[joint_id])] = float(value)
    for joint_name in ["finger_joint1", "finger_joint2"]:
        joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        data.qpos[int(model.jnt_qposadr[joint_id])] = finger_opening
    mujoco.mj_forward(model, data)


def set_base_qpos(model: mujoco.MjModel, data: mujoco.MjData, base_pose: np.ndarray) -> None:
    for joint_name, value in [
        ("mobile_base_x", base_pose[0] - MOBILE_BASE_START[0]),
        ("mobile_base_y", base_pose[1] - MOBILE_BASE_START[1]),
        ("mobile_base_yaw", base_pose[2]),
    ]:
        joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        data.qpos[int(model.jnt_qposadr[joint_id])] = float(value)


def set_finger_qpos(model: mujoco.MjModel, data: mujoco.MjData, opening: float) -> None:
    for joint_name in ["finger_joint1", "finger_joint2"]:
        joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        data.qpos[int(model.jnt_qposadr[joint_id])] = float(opening)


def set_scene_qpos(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    base_pose: np.ndarray,
    panda_qpos: np.ndarray,
    finger_opening: float,
    right_hinge_angle: float = 0.0,
) -> None:
    set_base_qpos(model, data, base_pose)
    hinge_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, RIGHT_HINGE_JOINT)
    data.qpos[int(model.jnt_qposadr[hinge_id])] = float(right_hinge_angle)
    for joint_index, value in enumerate(panda_qpos, start=1):
        joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, f"joint{joint_index}")
        data.qpos[int(model.jnt_qposadr[joint_id])] = float(value)
    set_finger_qpos(model, data, finger_opening)
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_task_xml()

    model = mujoco.MjModel.from_xml_path(str(TASK_XML))
    data = mujoco.MjData(model)

    handle_id = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, RIGHT_HANDLE_GEOM)
    grasp_proxy_id = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, RIGHT_HANDLE_GRASP_PROXY_GEOM)
    mobile_base_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "mobile_panda_base")
    left_finger_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")
    right_finger_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")
    hand_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "hand")
    link7_id = obj_id(model, mujoco.mjtObj.mjOBJ_BODY, "link7")

    set_panda_qpos(model, data, PANDA_HOME)
    save(IMAGE_DIR / "panda_reach_cabinet_start_top.png", render(model, data, "top"))

    frames: list[Image.Image] = []
    max_cabinet_contact_count = 0
    min_cabinet_contact_dist: float | None = None
    max_handle_finger_contact_count = 0
    max_handle_unique_finger_contact_count = 0
    max_handle_hand_contact_count = 0

    def record_contact_stats() -> None:
        nonlocal max_cabinet_contact_count
        nonlocal min_cabinet_contact_dist
        nonlocal max_handle_finger_contact_count
        nonlocal max_handle_unique_finger_contact_count
        nonlocal max_handle_hand_contact_count
        contact_count, contact_dist = cabinet_contact_stats(model, data)
        handle_contacts = handle_contact_stats(model, data, grasp_proxy_id)
        max_handle_finger_contact_count = max(
            max_handle_finger_contact_count,
            int(handle_contacts["finger_count"]),
        )
        max_handle_unique_finger_contact_count = max(
            max_handle_unique_finger_contact_count,
            int(handle_contacts["unique_finger_count"]),
        )
        max_handle_hand_contact_count = max(
            max_handle_hand_contact_count,
            int(handle_contacts["hand_count"]),
        )
        max_cabinet_contact_count = max(max_cabinet_contact_count, contact_count)
        if contact_dist is not None:
            min_cabinet_contact_dist = (
                contact_dist
                if min_cabinet_contact_dist is None
                else min(min_cabinet_contact_dist, contact_dist)
            )

    for step, alpha in enumerate(np.linspace(0.0, 1.0, 120)):
        smooth_alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        base_pose = (1.0 - smooth_alpha) * MOBILE_BASE_START + smooth_alpha * MOBILE_BASE_GOAL
        set_scene_qpos(model, data, base_pose, PANDA_HOME, FINGER_OPEN_START)
        record_contact_stats()
        if step % 10 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

    current_arm_qpos = PANDA_HOME.copy()
    for joint_offset in ARM_STAGE_ORDER:
        next_arm_qpos = current_arm_qpos.copy()
        next_arm_qpos[joint_offset] = PANDA_REACH[joint_offset]
        for step, alpha in enumerate(np.linspace(0.0, 1.0, 32)):
            smooth_alpha = alpha * alpha * (3.0 - 2.0 * alpha)
            target = (1.0 - smooth_alpha) * current_arm_qpos + smooth_alpha * next_arm_qpos
            set_scene_qpos(model, data, MOBILE_BASE_GOAL, target, FINGER_OPEN_START)
            record_contact_stats()
            if step % 8 == 0:
                frames.append(Image.fromarray(render(model, data, "top")))
        current_arm_qpos = next_arm_qpos

    for step, alpha in enumerate(np.linspace(0.0, 1.0, 70)):
        smooth_alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        finger_opening = (1.0 - smooth_alpha) * FINGER_OPEN_START + smooth_alpha * FINGER_OPEN_FINAL
        set_scene_qpos(model, data, MOBILE_BASE_GOAL, PANDA_REACH, finger_opening)
        record_contact_stats()
        if step % 10 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

    for step, alpha in enumerate(np.linspace(0.0, 1.0, 95)):
        smooth_alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        target = (1.0 - smooth_alpha) * PANDA_REACH + smooth_alpha * PANDA_PULL_OPEN
        hinge_angle = smooth_alpha * RIGHT_CABINET_PULL_ANGLE
        set_scene_qpos(
            model,
            data,
            MOBILE_BASE_GOAL,
            target,
            FINGER_OPEN_FINAL,
            right_hinge_angle=hinge_angle,
        )
        record_contact_stats()
        if step % 10 == 0:
            frames.append(Image.fromarray(render(model, data, "top")))

    pull_handle_pos = data.geom_xpos[handle_id].copy()
    pull_grasp_proxy_pos = data.geom_xpos[grasp_proxy_id].copy()
    pull_left_finger_pos = data.xpos[left_finger_id].copy()
    pull_right_finger_pos = data.xpos[right_finger_id].copy()
    pull_hand_pos = data.xpos[hand_id].copy()
    pull_link7_pos = data.xpos[link7_id].copy()
    pull_base_pos = data.xpos[mobile_base_id].copy()
    pull_base_goal_distance = float(np.linalg.norm(pull_base_pos[:2] - MOBILE_BASE_GOAL[:2]))
    pull_gripper_pos = ((pull_left_finger_pos + pull_right_finger_pos) / 2.0).copy()
    pull_distance = float(np.linalg.norm(pull_gripper_pos - pull_handle_pos))
    pull_grasp_proxy_distance = float(np.linalg.norm(pull_gripper_pos - pull_grasp_proxy_pos))
    pull_finger_y_straddles_grasp_proxy = bool(
        min(pull_left_finger_pos[1], pull_right_finger_pos[1]) <= pull_grasp_proxy_pos[1]
        <= max(pull_left_finger_pos[1], pull_right_finger_pos[1])
    )
    pull_finger_xy_separation = float(
        np.linalg.norm((pull_right_finger_pos - pull_left_finger_pos)[:2])
    )
    pull_finger_z_separation = float(abs(pull_right_finger_pos[2] - pull_left_finger_pos[2]))
    pull_finger_lateral_grasp_like = bool(
        pull_finger_y_straddles_grasp_proxy
        and pull_finger_xy_separation >= 0.04
        and pull_finger_z_separation <= 0.015
    )
    pull_fingers_outside_door_face = bool(
        max(pull_left_finger_pos[0], pull_right_finger_pos[0], pull_hand_pos[0]) < DOOR_FACE_MIN_X
    )
    pull_link7_inside_door_slab_bbox = bool(
        4.895 <= pull_link7_pos[0] <= 4.930
        and 2.490 <= pull_link7_pos[1] <= 2.947
        and 0.140 <= pull_link7_pos[2] <= 1.260
    )
    pull_terminal_chain_visual_clearance_passed = bool(
        pull_fingers_outside_door_face
        and not pull_link7_inside_door_slab_bbox
    )
    pull_cabinet_contact_count, pull_cabinet_contact_dist = cabinet_contact_stats(model, data)
    pull_handle_contacts = handle_contact_stats(model, data, grasp_proxy_id)
    right_hinge_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, RIGHT_HINGE_JOINT)
    pull_hinge_angle = float(data.qpos[int(model.jnt_qposadr[right_hinge_id])])

    follow_start = np.concatenate([[RIGHT_CABINET_PULL_ANGLE], MOBILE_BASE_GOAL, PANDA_PULL_OPEN])
    follow_waypoints = np.vstack([follow_start, PANDA_FOLLOW_90_WAYPOINTS])
    for waypoint_a, waypoint_b in zip(follow_waypoints[:-1], follow_waypoints[1:]):
        angle_a = float(waypoint_a[0])
        angle_b = float(waypoint_b[0])
        base_a = waypoint_a[1:4]
        base_b = waypoint_b[1:4]
        qpos_a = waypoint_a[4:11]
        qpos_b = waypoint_b[4:11]
        for step, alpha in enumerate(np.linspace(0.0, 1.0, 24)):
            smooth_alpha = alpha * alpha * (3.0 - 2.0 * alpha)
            hinge_angle = (1.0 - smooth_alpha) * angle_a + smooth_alpha * angle_b
            base_pose = (1.0 - smooth_alpha) * base_a + smooth_alpha * base_b
            panda_qpos = (1.0 - smooth_alpha) * qpos_a + smooth_alpha * qpos_b
            set_scene_qpos(
                model,
                data,
                base_pose,
                panda_qpos,
                FINGER_OPEN_FINAL,
                right_hinge_angle=hinge_angle,
            )
            record_contact_stats()
            if step % 8 == 0:
                frames.append(Image.fromarray(render(model, data, "top")))

    if not frames:
        frames.append(Image.fromarray(render(model, data, "top")))

    handle_pos = data.geom_xpos[handle_id].copy()
    grasp_proxy_pos = data.geom_xpos[grasp_proxy_id].copy()
    base_pos = data.xpos[mobile_base_id].copy()
    base_goal_distance = float(np.linalg.norm(base_pos[:2] - MOBILE_BASE_GOAL[:2]))
    left_finger_pos = data.xpos[left_finger_id].copy()
    right_finger_pos = data.xpos[right_finger_id].copy()
    hand_pos = data.xpos[hand_id].copy()
    link7_pos = data.xpos[link7_id].copy()
    gripper_pos = ((left_finger_pos + right_finger_pos) / 2.0).copy()
    distance = float(np.linalg.norm(gripper_pos - handle_pos))
    grasp_proxy_distance = float(np.linalg.norm(gripper_pos - grasp_proxy_pos))
    standoff_distance = float(np.linalg.norm(gripper_pos - HANDLE_STANDOFF_TARGET))
    finger_y_straddles_handle = bool(
        min(left_finger_pos[1], right_finger_pos[1]) <= handle_pos[1]
        <= max(left_finger_pos[1], right_finger_pos[1])
    )
    finger_y_straddles_grasp_proxy = bool(
        min(left_finger_pos[1], right_finger_pos[1]) <= grasp_proxy_pos[1]
        <= max(left_finger_pos[1], right_finger_pos[1])
    )
    finger_xy_separation = float(np.linalg.norm((right_finger_pos - left_finger_pos)[:2]))
    finger_z_separation = float(abs(right_finger_pos[2] - left_finger_pos[2]))
    finger_lateral_grasp_like = bool(
        finger_y_straddles_grasp_proxy
        and finger_xy_separation >= 0.04
        and finger_z_separation <= 0.015
    )
    fingers_outside_door_face = bool(max(left_finger_pos[0], right_finger_pos[0], hand_pos[0]) < DOOR_FACE_MIN_X)
    link7_inside_door_slab_bbox = bool(
        4.895 <= link7_pos[0] <= 4.930
        and 2.490 <= link7_pos[1] <= 2.947
        and 0.140 <= link7_pos[2] <= 1.260
    )
    terminal_chain_visual_clearance_passed = bool(
        fingers_outside_door_face
        and not link7_inside_door_slab_bbox
    )
    cabinet_contact_count, final_cabinet_contact_dist = cabinet_contact_stats(model, data)
    final_handle_contacts = handle_contact_stats(model, data, grasp_proxy_id)
    right_hinge_angle = float(data.qpos[int(model.jnt_qposadr[right_hinge_id])])
    finger_joint_positions = []
    for joint_name in ["finger_joint1", "finger_joint2"]:
        joint_id = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        finger_joint_positions.append(float(data.qpos[int(model.jnt_qposadr[joint_id])]))
    all_finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
    passed = bool(
        pull_base_goal_distance <= 0.09
        and pull_distance <= 0.12
        and pull_grasp_proxy_distance <= 0.12
        and int(pull_handle_contacts["unique_finger_count"]) >= 2
        and max_handle_unique_finger_contact_count >= 2
        and pull_finger_lateral_grasp_like
        and pull_hinge_angle >= RIGHT_CABINET_PULL_ANGLE - 0.01
        and right_hinge_angle >= RIGHT_CABINET_OPEN_ANGLE - 0.01
        and pull_terminal_chain_visual_clearance_passed
        and terminal_chain_visual_clearance_passed
        and (final_cabinet_contact_dist is None or final_cabinet_contact_dist > -0.003)
        and (min_cabinet_contact_dist is None or min_cabinet_contact_dist > -0.01)
        and all_finite
    )

    save(IMAGE_DIR / "panda_reach_cabinet_final_top.png", render(model, data, "top"))
    save(IMAGE_DIR / "panda_reach_cabinet_final_diag.png", render(model, data, "diag"))
    gif_path = VIDEO_DIR / "panda_reach_cabinet_handle.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=120, loop=0)

    summary = {
        "task_name": "mobile_panda_reach_cabinet_handle",
        "scene_xml": str(TASK_XML),
        "robot": "franka_emika_panda",
        "robot_note": "Franka Panda mounted on a simplified x/y/yaw mobile base. This is a prototype mobile-manipulation sequence, not a realistic wheel model yet.",
        "base_pos": PANDA_BASE_POS,
        "base_quat": PANDA_BASE_QUAT,
        "mobile_base_start": [float(v) for v in MOBILE_BASE_START],
        "mobile_base_goal": [float(v) for v in MOBILE_BASE_GOAL],
        "mobile_base_final_position": [float(v) for v in base_pos],
        "mobile_base_goal_distance": base_goal_distance,
        "target_handle_geom": RIGHT_HANDLE_GEOM,
        "target_grasp_proxy_geom": RIGHT_HANDLE_GRASP_PROXY_GEOM,
        "handle_position": [float(v) for v in handle_pos],
        "grasp_proxy_position": [float(v) for v in grasp_proxy_pos],
        "handle_standoff_target": [float(v) for v in HANDLE_STANDOFF_TARGET],
        "gripper_position": [float(v) for v in gripper_pos],
        "left_finger_position": [float(v) for v in left_finger_pos],
        "right_finger_position": [float(v) for v in right_finger_pos],
        "hand_position": [float(v) for v in hand_pos],
        "link7_position": [float(v) for v in link7_pos],
        "gripper_to_handle_distance": distance,
        "gripper_to_grasp_proxy_distance": grasp_proxy_distance,
        "gripper_to_standoff_distance": standoff_distance,
        "pull_handle_position": [float(v) for v in pull_handle_pos],
        "pull_grasp_proxy_position": [float(v) for v in pull_grasp_proxy_pos],
        "pull_mobile_base_position": [float(v) for v in pull_base_pos],
        "pull_mobile_base_goal_distance": pull_base_goal_distance,
        "pull_gripper_position": [float(v) for v in pull_gripper_pos],
        "pull_gripper_to_handle_distance": pull_distance,
        "pull_gripper_to_grasp_proxy_distance": pull_grasp_proxy_distance,
        "pull_finger_y_straddles_grasp_proxy": pull_finger_y_straddles_grasp_proxy,
        "pull_finger_xy_separation": pull_finger_xy_separation,
        "pull_finger_z_separation": pull_finger_z_separation,
        "pull_finger_lateral_grasp_like": pull_finger_lateral_grasp_like,
        "pull_fingers_outside_door_face": pull_fingers_outside_door_face,
        "pull_link7_inside_door_slab_bbox": pull_link7_inside_door_slab_bbox,
        "pull_terminal_chain_visual_clearance_passed": pull_terminal_chain_visual_clearance_passed,
        "pull_handle_finger_contact_count": int(pull_handle_contacts["finger_count"]),
        "pull_handle_unique_finger_contact_count": int(pull_handle_contacts["unique_finger_count"]),
        "pull_handle_finger_contact_bodies": pull_handle_contacts["finger_bodies"],
        "pull_handle_hand_contact_count": int(pull_handle_contacts["hand_count"]),
        "pull_handle_contact_bodies": pull_handle_contacts["bodies"],
        "pull_handle_contact_min_dist": pull_handle_contacts["min_dist"],
        "pull_cabinet_contact_count": pull_cabinet_contact_count,
        "pull_cabinet_contact_min_dist": pull_cabinet_contact_dist,
        "success_distance": SUCCESS_DISTANCE,
        "finger_y_straddles_handle": finger_y_straddles_handle,
        "finger_y_straddles_grasp_proxy": finger_y_straddles_grasp_proxy,
        "finger_xy_separation": finger_xy_separation,
        "finger_z_separation": finger_z_separation,
        "finger_lateral_grasp_like": finger_lateral_grasp_like,
        "fingers_outside_door_face": fingers_outside_door_face,
        "door_face_min_x": DOOR_FACE_MIN_X,
        "link7_inside_door_slab_bbox": link7_inside_door_slab_bbox,
        "terminal_chain_visual_clearance_passed": terminal_chain_visual_clearance_passed,
        "handle_finger_contact_count_final": int(final_handle_contacts["finger_count"]),
        "handle_unique_finger_contact_count_final": int(final_handle_contacts["unique_finger_count"]),
        "handle_finger_contact_bodies_final": final_handle_contacts["finger_bodies"],
        "handle_hand_contact_count_final": int(final_handle_contacts["hand_count"]),
        "handle_contact_bodies_final": final_handle_contacts["bodies"],
        "handle_contact_min_dist_final": final_handle_contacts["min_dist"],
        "handle_finger_contact_count_max_over_motion": max_handle_finger_contact_count,
        "handle_unique_finger_contact_count_max_over_motion": max_handle_unique_finger_contact_count,
        "handle_hand_contact_count_max_over_motion": max_handle_hand_contact_count,
        "finger_joint_positions_final": finger_joint_positions,
        "cabinet_contact_count_final": cabinet_contact_count,
        "cabinet_contact_count_max_over_motion": max_cabinet_contact_count,
        "cabinet_contact_min_dist_final": final_cabinet_contact_dist,
        "cabinet_contact_min_dist_over_motion": min_cabinet_contact_dist,
        "right_hinge_joint": RIGHT_HINGE_JOINT,
        "right_hinge_pull_target": RIGHT_CABINET_PULL_ANGLE,
        "right_hinge_pull_angle": pull_hinge_angle,
        "right_hinge_angle_final": right_hinge_angle,
        "right_hinge_open_target": RIGHT_CABINET_OPEN_ANGLE,
        "panda_home_qpos": [float(v) for v in PANDA_HOME],
        "panda_reach_qpos": [float(v) for v in PANDA_REACH],
        "panda_pull_open_qpos": [float(v) for v in PANDA_PULL_OPEN],
        "panda_follow_90_waypoints": [[float(v) for v in row] for row in PANDA_FOLLOW_90_WAYPOINTS],
        "task_sequence_note": "Base moves to the cabinet, Panda side-grasps the handle, pulls to 0.50 rad, then the mobile base and arm follow optimized waypoints so the gripper stays near the moving handle until the cabinet door reaches 90 degrees. This is still a kinematic qpos prototype, not a force-controlled dynamic grasp.",
        "all_finite": all_finite,
        "contact_count_final": int(data.ncon),
        "passed": passed,
        "outputs": {
            "start_top": str(IMAGE_DIR / "panda_reach_cabinet_start_top.png"),
            "final_top": str(IMAGE_DIR / "panda_reach_cabinet_final_top.png"),
            "final_diag": str(IMAGE_DIR / "panda_reach_cabinet_final_diag.png"),
            "motion_gif": str(gif_path),
        },
    }
    (RESULT_DIR / "panda_reach_cabinet_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
