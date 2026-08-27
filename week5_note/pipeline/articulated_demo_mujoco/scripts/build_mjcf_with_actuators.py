#!/usr/bin/env python3
"""Add MuJoCo actuators to the reconstructed articulated demo room joints."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_XML = ROOT / "xml" / "articulated_demo_with_joints.xml"
OUTPUT_XML = ROOT / "xml" / "articulated_demo_with_actuators.xml"
SUMMARY_PATH = ROOT / "outputs" / "actuator_build_summary.json"

ACTUATORS = [
    ("frame_to_door_pos", "frame_to_door", "0 1.5708", "8"),
    ("left_hinge_pos", "left_hinge", "0 1.5708", "8"),
    ("right_hinge_pos", "right_hinge", "0 1.5708", "8"),
    ("body_to_front_door_pos", "body_to_front_door", "0 1.75", "8"),
    ("body_to_sliding_tray_pos", "body_to_sliding_tray", "0 0.22", "18"),
    ("tray_to_turntable_pos", "tray_to_turntable", "-6.2832 6.2832", "3"),
    ("body_to_upper_knob_pos", "body_to_upper_knob", "-3.1416 3.1416", "3"),
    ("body_to_lower_knob_pos", "body_to_lower_knob", "-3.1416 3.1416", "3"),
]


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
    root.set("model", "articulated_demo_room_with_actuators")

    existing = root.find("actuator")
    if existing is not None:
        root.remove(existing)

    actuator = ET.SubElement(root, "actuator")
    for name, joint, ctrlrange, kp in ACTUATORS:
        ET.SubElement(
            actuator,
            "position",
            {
                "name": name,
                "joint": joint,
                "ctrlrange": ctrlrange,
                "kp": kp,
            },
        )

    indent(root)
    tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)

    summary = {
        "input_xml": str(INPUT_XML),
        "output_xml": str(OUTPUT_XML),
        "actuator_count": len(ACTUATORS),
        "actuators": [
            {"name": name, "joint": joint, "ctrlrange": ctrlrange, "kp": kp}
            for name, joint, ctrlrange, kp in ACTUATORS
        ],
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
