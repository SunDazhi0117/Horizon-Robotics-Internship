# Level 2 Handle-Follow Opening Report

## Outcome

Level 2 is the validated handle-follow cabinet-opening result.

It starts from the accepted Level 1 no-visual-overlap grasp. At the closed-door pose, the script records the Panda hand transform relative to the right cabinet door. For each opening angle, inverse kinematics solves the mobile-base and seven Panda joint positions while preserving that relative transform.

This prevents the clearance optimizer from moving the gripper away from the handle, which was the main failure in the preceding experiment.

## Outputs

- Script: `scripts/run_level_2_handle_follow_open_90.py`
- Diagonal GIF: `assets/videos/level_2_handle_follow_open_90.gif`
- Top-view GIF: `assets/videos/level_2_handle_follow_open_90_top_view.gif`
- Summary: `assets/results/level_2_handle_follow_open_90_summary.json`
- Solved trajectory: `assets/results/level_2_handle_follow_open_90_trajectory.json`
- Close-up contact sheet: `assets/images/level_2_handle_follow_open_90_contact_sheet.png`

## Validation

- Full validation: `PASS`
- Opening samples: `49`
- Final hinge angle: `1.57079632679 rad`
- Maximum gripper-to-handle distance: `0.0532052 m`
- Minimum unique finger contacts: `2`
- Maximum hand position tracking error: `1.49e-7 m`
- Maximum hand rotation tracking error: `7.27e-7 rad`
- Visual-overlap failure count: `0`
- Forbidden handle-contact failure count: `0`
- Door-slab contact failure count: `0`

## Visual Review

Diagonal, top-view, and nine close-up opening frames were reviewed. The handle remains between the two fingers from the closed pose to 90 degrees. No hard video splice, mid-motion wrist flip, visible handle detachment, or cabinet-door penetration was found in the reviewed frames.

## Scope

Level 2 validates approach, grasp, and opening to 90 degrees. It does not yet close the cabinet again. A future closed-loop task should reverse or separately solve the same rigid handle-follow trajectory and repeat the full validation in both directions.
