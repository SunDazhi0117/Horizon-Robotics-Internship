# Week6 Final Panda Open-Close Cabinet

## Directory

`week6_note`

## Goal

Fix the current best Panda cabinet interaction as a stable Week6 artifact.

The demo shows:

1. Panda moves from the start pose to the cabinet handle area.
2. The arm rotates into a horizontal side-grasp pose.
3. The gripper closes around the supported visible cabinet handle.
4. The right cabinet door opens to 90 degrees.
5. The robot follows the same handle path in reverse.
6. The right cabinet door closes back to 0 degrees.
7. The gripper releases the handle.

## Included Artifacts

- Motion GIF: `assets/videos/panda_open_close_cabinet.gif`
- Summary JSON: `assets/results/panda_open_close_cabinet_summary.json`
- Open-pose image: `assets/images/panda_open_close_cabinet_open_diag.png`
- Final closed image: `assets/images/panda_open_close_cabinet_closed_final_diag.png`
- Final top image: `assets/images/panda_open_close_cabinet_closed_final_top.png`
- Frame sheet: `assets/images/panda_open_close_cabinet_frames_sheet.png`
- Main script snapshot: `scripts/run_panda_open_close_cabinet.py`
- Helper script snapshots:
  - `scripts/run_panda_handle_pull_90_attempt.py`
  - `scripts/run_panda_handle_pull_minimal.py`
  - `scripts/run_panda_reach_cabinet_handle.py`
- Scene XML snapshot: `xml/articulated_demo_room_with_panda_minimal_handle_pull.xml`

## Numeric Validation

- Numeric result: `PASS`
- Target open hinge angle: `1.5708 rad`
- Max hinge angle reached: `1.5708 rad`
- Final closed hinge angle: `0.0000 rad`
- Open-pose gripper-to-handle distance: `0.00037 m`
- Closed-pose gripper-to-handle distance: `0.000001 m`
- Max gripper-to-handle distance during validated motion: `0.0064 m`
- Max tool-axis vertical component: `0.0059`
- Max finger height difference: `0.00022 m`
- Min horizontal finger separation: `0.0380 m`
- Grasp finger opening: `0.019 m`
- Open-pose unique finger contacts on visible handle: `2`
- Closed-pose unique finger contacts on visible handle: `2`
- Forbidden door-slab contact count: `0`

## Visual Review Notes

Initial visual inspection showed:

- The gripper stays visually aligned with the supported handle.
- The cabinet opens to approximately 90 degrees.
- The cabinet closes back to its original pose.
- The arm does not visibly pass through the cabinet door slab in the sampled frame sheet.
- The handle is supported by visual-only brackets, so it no longer reads as floating.
- The Panda is mounted on a visual-only unicycle-style mobile base.

The user should still visually inspect the GIF for:

- subtle finger/handle separation,
- subtle door/hand overlap,
- arm/cabinet collision from angles not shown in the frame sheet,
- unnatural timing or motion.

## Important Limitation

This is a scripted qpos waypoint prototype.

It is not yet:

- force-controlled grasping,
- autonomous motion planning,
- real contact-rich cabinet manipulation,
- a robot policy,
- a full benchmark task.

The value of this version is that it gives a stable, inspectable open-close cabinet behavior that can be used as a reference for later planning and control work.

## Viewer

Main Week6 viewer:

`http://127.0.0.1:8899/week6_note/`

Direct GIF path:

`http://127.0.0.1:8899/week6_note/assets/videos/panda_open_close_cabinet.gif`

## Status

This is the retained Week6 closed-loop result.
