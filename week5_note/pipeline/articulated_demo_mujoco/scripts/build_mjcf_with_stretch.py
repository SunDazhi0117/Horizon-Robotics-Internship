#!/usr/bin/env python3
"""Merge the real Hello Robot Stretch MJCF into the articulated demo room."""

from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOM_XML = ROOT / "xml" / "articulated_demo_with_actuators.xml"
STRETCH_DIR = ROOT.parents[1] / "external" / "mujoco_menagerie" / "hello_robot_stretch"
STRETCH_XML = STRETCH_DIR / "stretch.xml"
OUTPUT_XML = ROOT / "xml" / "articulated_demo_with_stretch.xml"
SUMMARY_PATH = ROOT / "outputs" / "stretch_room_build_summary.json"


def indent(element: ET.Element, level: int = 0) -> None:
    pad = "\n" + level * "  "
    if len(element):
        if not element.text or not element.text.strip():
            element.text = pad + "  "
        for child in element:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = pad
    if level and (not element.tail or not element.tail.strip()):
        element.tail = pad


def rewrite_asset_files(element: ET.Element) -> None:
    for child in element.iter():
        file_name = child.get("file")
        if file_name:
            child.set("file", str((STRETCH_DIR / "assets" / file_name).resolve()))


def main() -> None:
    if not ROOM_XML.exists():
        raise FileNotFoundError(ROOM_XML)
    if not STRETCH_XML.exists():
        raise FileNotFoundError(STRETCH_XML)

    room_tree = ET.parse(ROOM_XML)
    room_root = room_tree.getroot()
    room_root.set("model", "articulated_demo_room_with_stretch")

    stretch_root = ET.parse(STRETCH_XML).getroot()

    stretch_option = stretch_root.find("option")
    if stretch_option is not None:
        old_option = room_root.find("option")
        if old_option is not None:
            insert_index = list(room_root).index(old_option)
            room_root.remove(old_option)
            room_root.insert(insert_index, copy.deepcopy(stretch_option))
        else:
            room_root.insert(1, copy.deepcopy(stretch_option))

    room_asset = room_root.find("asset")
    room_worldbody = room_root.find("worldbody")
    if room_asset is None or room_worldbody is None:
        raise RuntimeError("Room XML must have asset and worldbody")

    stretch_default = stretch_root.find("default")
    if stretch_default is not None:
        old_default = room_root.find("default")
        if old_default is not None:
            room_root.remove(old_default)
        room_root.insert(3, copy.deepcopy(stretch_default))

    stretch_asset = stretch_root.find("asset")
    if stretch_asset is None:
        raise RuntimeError("Stretch XML must have asset")
    for asset_child in list(stretch_asset):
        copied = copy.deepcopy(asset_child)
        rewrite_asset_files(copied)
        room_asset.append(copied)

    for section_name in ["contact", "tendon", "equality"]:
        stretch_section = stretch_root.find(section_name)
        if stretch_section is None:
            continue
        old_section = room_root.find(section_name)
        if old_section is not None:
            room_root.remove(old_section)
        room_root.append(copy.deepcopy(stretch_section))

    # Give the real robot a collision floor while keeping the rendered room floor.
    if room_worldbody.find("./geom[@name='stretch_collision_floor']") is None:
        ET.SubElement(
            room_worldbody,
            "geom",
            {
                "name": "stretch_collision_floor",
                "type": "plane",
                "size": "0 0 0.05",
                "rgba": "0.1 0.1 0.1 1",
            },
        )

    stretch_worldbody = stretch_root.find("worldbody")
    if stretch_worldbody is None:
        raise RuntimeError("Stretch XML must have worldbody")
    stretch_body = stretch_worldbody.find("./body[@name='base_link']")
    if stretch_body is None:
        raise RuntimeError("Could not find Stretch base_link body")

    old_robot = room_worldbody.find("./body[@name='base_link']")
    if old_robot is not None:
        room_worldbody.remove(old_robot)
    robot = copy.deepcopy(stretch_body)
    robot.set("pos", "2.6 2.0 0")
    room_worldbody.append(robot)

    room_actuator = room_root.find("actuator")
    if room_actuator is None:
        room_actuator = ET.SubElement(room_root, "actuator")
    stretch_actuator = stretch_root.find("actuator")
    if stretch_actuator is not None:
        existing_names = {child.get("name") for child in room_actuator}
        for actuator_child in list(stretch_actuator):
            if actuator_child.get("name") not in existing_names:
                room_actuator.append(copy.deepcopy(actuator_child))

    indent(room_root)
    room_tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)

    summary = {
        "input_room_xml": str(ROOM_XML),
        "stretch_xml": str(STRETCH_XML),
        "output_xml": str(OUTPUT_XML),
        "robot_body": "base_link",
        "robot_initial_pos": [2.6, 2.0, 0.0],
        "note": "Merged real Hello Robot Stretch MJCF into the actuator-enabled articulated room.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
