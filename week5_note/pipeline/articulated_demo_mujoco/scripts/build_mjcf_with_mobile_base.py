#!/usr/bin/env python3
"""Add a simple controllable mobile base to the actuator-enabled room."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_XML = ROOT / "xml" / "articulated_demo_with_actuators.xml"
OUTPUT_XML = ROOT / "xml" / "articulated_demo_with_mobile_base.xml"
SUMMARY_PATH = ROOT / "outputs" / "mobile_base_build_summary.json"


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


def main() -> None:
    if not INPUT_XML.exists():
        raise FileNotFoundError(INPUT_XML)

    tree = ET.parse(INPUT_XML)
    root = tree.getroot()
    root.set("model", "articulated_demo_room_with_mobile_base")

    worldbody = root.find("worldbody")
    if worldbody is None:
        raise RuntimeError("Missing worldbody")

    existing = worldbody.find("./body[@name='simple_mobile_base']")
    if existing is not None:
        worldbody.remove(existing)

    robot = ET.SubElement(worldbody, "body", {"name": "simple_mobile_base", "pos": "2.6 2.0 0.16"})
    ET.SubElement(robot, "inertial", {"pos": "0 0 0", "mass": "8", "diaginertia": "0.15 0.15 0.12"})
    ET.SubElement(robot, "joint", {"name": "base_x", "type": "slide", "axis": "1 0 0", "range": "-1.5 1.5", "damping": "2"})
    ET.SubElement(robot, "joint", {"name": "base_y", "type": "slide", "axis": "0 1 0", "range": "-1.2 1.2", "damping": "2"})
    ET.SubElement(robot, "joint", {"name": "base_yaw", "type": "hinge", "axis": "0 0 1", "range": "-3.1416 3.1416", "damping": "1"})
    ET.SubElement(robot, "geom", {"name": "base_body", "type": "cylinder", "size": "0.22 0.08", "rgba": "0.2 0.55 0.9 1"})
    ET.SubElement(robot, "geom", {"name": "base_front_marker", "type": "box", "pos": "0.22 0 0.05", "size": "0.04 0.08 0.035", "rgba": "1 0.85 0.2 1"})

    actuator = root.find("actuator")
    if actuator is None:
        actuator = ET.SubElement(root, "actuator")
    for name in ["base_x_pos", "base_y_pos", "base_yaw_pos"]:
        old = actuator.find(f"./position[@name='{name}']")
        if old is not None:
            actuator.remove(old)
    ET.SubElement(actuator, "position", {"name": "base_x_pos", "joint": "base_x", "ctrlrange": "-1.5 1.5", "kp": "18"})
    ET.SubElement(actuator, "position", {"name": "base_y_pos", "joint": "base_y", "ctrlrange": "-1.2 1.2", "kp": "18"})
    ET.SubElement(actuator, "position", {"name": "base_yaw_pos", "joint": "base_yaw", "ctrlrange": "-3.1416 3.1416", "kp": "8"})

    indent(root)
    tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)

    summary = {
        "input_xml": str(INPUT_XML),
        "output_xml": str(OUTPUT_XML),
        "robot": "simple_mobile_base",
        "robot_joints": ["base_x", "base_y", "base_yaw"],
        "robot_actuators": ["base_x_pos", "base_y_pos", "base_yaw_pos"],
        "note": "Minimal geometric mobile base, not a real robot URDF.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
