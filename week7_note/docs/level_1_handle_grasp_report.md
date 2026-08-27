# Level 1 Handle-Grasp Report

## Task

`level_1_handle_grasp`

## Why This Level Was Added

The previous side-grasp experiment still had visible penetration in the top view.

The issue was not only MuJoCo contact. Some rendered Panda visual geoms could overlap the handle even when physical contact validation passed.

This level uses an RRT-found joint path to avoid the visible hand/handle overlap.

## Main Files

- Script: `scripts/run_level_1_handle_grasp.py`
- Diagonal GIF: `assets/videos/level_1_handle_grasp.gif`
- Top-view GIF: `assets/videos/level_1_handle_grasp_top_view.gif`
- Summary: `assets/results/level_1_handle_grasp_summary.json`
- Frame sheet: `assets/images/level_1_handle_grasp_frames_sheet.png`
- Top-view frame sheet: `assets/images/level_1_handle_grasp_top_frames_sheet.png`

## Validation Result

Result: `PASS`

Key metrics:

- Samples checked: `351`
- Forbidden handle-contact events: `0`
- Visual overlap events: `0`
- Final finger contact bodies: `left_finger`, `right_finger`
- Final finger contact count: `2`
- Final gripper-to-handle distance: `0.0532051618 m`
- Final finger z-separation: `0.0001268499 m`

## What This Means

This is the current no-visual-overlap grasp level.

It passes:

- MuJoCo contact validation,
- visual OBB overlap validation,
- final two-finger handle contact validation.

## Limitation

This is still only the grasp subtask.

It does not open the cabinet yet.

## Next Step

Use this Level 1 grasp path as the starting point for the cabinet-opening trajectory.
