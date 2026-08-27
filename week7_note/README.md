# Week7 Note: MuJoCo Cabinet Manipulation

This directory contains only the five retained cabinet-manipulation levels.

## Code Learning

The beginner-oriented Chinese code guide starts here:

- [Python and MuJoCo task code learning guide](code_learning/README.md)
- [Project-specific Python basics](code_learning/00_python_basics.md)
- [Reusable task-system implementation](code_learning/08_generalization_implementation.md)

The guide explains the Level 5 task from Python syntax through trajectory generation, inverse kinematics, collision validation, rendering, evaluation, and future task generalization.

## Representative Results

The five retained results are organized by task difficulty:

| Stage | Purpose | Result |
| --- | --- | --- |
| Level 1 | No-visual-overlap handle grasp | PASS |
| Level 2 | Maintain the grasp and open to 90 degrees | PASS |
| Level 3 | Keep the base fixed and open using only arm joints | PASS |
| Level 4 | Keep the base fixed, open to 90 degrees, and close again | PASS |
| Level 5 | Open the right door, reposition safely, then open the left door | PASS |

Viewer:

`http://127.0.0.1:8899/week7_note/`

## Main Videos

Level 1 handle grasp:

- `assets/videos/level_1_handle_grasp.gif`
- `assets/videos/level_1_handle_grasp_top_view.gif`

Level 2 handle-follow opening:

- `assets/videos/level_2_handle_follow_open_90.gif`
- `assets/videos/level_2_handle_follow_open_90_top_view.gif`

Level 3 fixed-base arm-only opening:

- `assets/videos/level_3_fixed_base_arm_only_open_90.gif`
- `assets/videos/level_3_fixed_base_arm_only_open_90_top_view.gif`

Level 4 fixed-base arm-only open-close:

- `assets/videos/level_4_fixed_base_arm_only_open_close.gif`
- `assets/videos/level_4_fixed_base_arm_only_open_close_top_view.gif`

Level 5 sequential double-door opening:

- `assets/videos/level_5_sequential_open_both_doors.gif`
- `assets/videos/level_5_sequential_open_both_doors_top_view.gif`
- `assets/videos/level_5_sequential_open_both_doors_right_side_view.gif`

## Main Images

The image directory contains the current Level 1 stills and Level 1-5 validation sheets:

- `assets/images/level_1_handle_grasp_final_diag.png`
- `assets/images/level_1_handle_grasp_final_top.png`
- `assets/images/level_1_handle_grasp_frames_sheet.png`
- `assets/images/level_1_handle_grasp_top_frames_sheet.png`
- `assets/images/level_2_handle_follow_open_90_frames_sheet.png`
- `assets/images/level_2_handle_follow_open_90_top_frames_sheet.png`
- `assets/images/level_2_handle_follow_open_90_contact_sheet.png`
- `assets/images/level_3_fixed_base_arm_only_open_90_frames_sheet.png`
- `assets/images/level_3_fixed_base_arm_only_open_90_top_frames_sheet.png`
- `assets/images/level_4_fixed_base_arm_only_open_close_frames_sheet.png`
- `assets/images/level_4_fixed_base_arm_only_open_close_top_frames_sheet.png`
- `assets/images/level_5_sequential_open_both_doors_frames_sheet.png`
- `assets/images/level_5_sequential_open_both_doors_top_frames_sheet.png`
- `assets/images/level_5_sequential_open_both_doors_right_side_frames_sheet.png`

## Level 2 Validation

- Final hinge angle: `1.57079632679 rad` (`90 deg`)
- Opening samples: `49`
- Minimum unique finger contacts: `2`
- Maximum gripper-to-handle distance: `0.0532052 m`
- Visual-overlap failures: `0`
- Forbidden handle-contact failures: `0`
- Door-slab collision failures: `0`
- Local RoboDojo-style deterministic score: `100/100`
- Official RoboDojo score: `N/A`

## Level 3 Validation

- Base motion during opening: locked
- Maximum base drift: `0.0`
- Final hinge angle: `1.57079632679 rad` (`90 deg`)
- Opening samples: `65`
- Minimum unique finger contacts: `2`
- Maximum gripper-to-handle distance: `0.0532051 m`
- Maximum arm-joint step: `0.1113531 rad`
- Visual-overlap failures: `0`
- Forbidden handle-contact failures: `0`
- Door-slab collision failures: `0`

## Level 4 Validation

- Base motion for the complete open-close task: locked
- Maximum base drift: `0.0`
- Maximum hinge angle: `1.57079632679 rad` (`90 deg`)
- Final closed hinge angle: `0.0 rad`
- Total validated states: `149`
- Minimum unique finger contacts: `2`
- Maximum gripper-to-handle distance: `0.0532051 m`
- Whole-cabinet visual-overlap failures: `0`
- Forbidden handle-contact failures: `0`
- Door-slab collision failures: `0`
- Local deterministic evaluation score: `100/100`

## Level 5 Validation

- Right door final angle: `1.57079632679 rad` (`90 deg`)
- Left door final angle: `1.57079632679 rad` (`90 deg`)
- Right-opening base drift: `0.0`
- Left opening uses a controlled base-and-arm retreat
- Base motion outside the transfer phases: `0`
- Door motion outside each assigned opening phase: `0`
- Right opening samples: `65`
- Left opening samples: `65`
- Total validated states: `429`
- Minimum right-handle finger contacts: `2`
- Minimum left-handle finger contacts: `2`
- Maximum joint step: `0.1113531 rad`
- Environment geometries checked: `93`
- Full-environment visual-overlap failures: `0`
- Forbidden active-handle contact failures: `0`
- Local deterministic evaluation score: `100/100`

## Reproduce

Generate and validate Level 1:

```bash
/home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
  scripts/run_level_1_handle_grasp.py
```

Generate and validate Level 2:

```bash
/home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
  scripts/run_level_2_handle_follow_open_90.py
```

Run the adapted RoboDojo-style evaluator:

```bash
python scripts/evaluate_level_2_handle_follow_open_90.py
```

Generate and validate Level 3:

```bash
/home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
  scripts/run_level_3_fixed_base_arm_only_open_90.py
```

Generate and validate Level 4:

```bash
/home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
  scripts/run_level_4_fixed_base_arm_only_open_close.py
```

Run the Level 4 evaluation:

```bash
python scripts/evaluate_level_4_fixed_base_arm_only_open_close.py
```

Generate and validate Level 5:

```bash
/home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
  scripts/run_level_5_sequential_open_both_doors.py
```

Run the Level 5 evaluation:

```bash
python scripts/evaluate_level_5_sequential_open_both_doors.py
```

## Main Files

- `scripts/run_level_1_handle_grasp.py`
- `scripts/level_validation_helpers.py`
- `assets/results/level_1_handle_grasp_summary.json`
- `scripts/run_level_2_handle_follow_open_90.py`
- `scripts/evaluate_level_2_handle_follow_open_90.py`
- `assets/results/level_2_handle_follow_open_90_summary.json`
- `assets/results/level_2_handle_follow_open_90_trajectory.json`
- `assets/results/level_2_handle_follow_open_90_evaluation.json`
- `scripts/run_level_3_fixed_base_arm_only_open_90.py`
- `assets/results/level_3_fixed_base_arm_only_open_90_summary.json`
- `assets/results/level_3_fixed_base_arm_only_open_90_trajectory.json`
- `scripts/run_level_4_fixed_base_arm_only_open_close.py`
- `scripts/evaluate_level_4_fixed_base_arm_only_open_close.py`
- `assets/results/level_4_fixed_base_arm_only_open_close_summary.json`
- `assets/results/level_4_fixed_base_arm_only_open_close_trajectory.json`
- `assets/results/level_4_fixed_base_arm_only_open_close_evaluation.json`
- `scripts/run_level_5_sequential_open_both_doors.py`
- `scripts/evaluate_level_5_sequential_open_both_doors.py`
- `xml/level_5_sequential_open_both_doors.xml`
- `assets/results/level_5_sequential_open_both_doors_summary.json`
- `assets/results/level_5_sequential_open_both_doors_trajectory.json`
- `assets/results/level_5_sequential_open_both_doors_evaluation.json`
- [Level 5 Evaluation Form](docs/level_5_sequential_open_both_doors_evaluation.md)
- [Level 4 Evaluation Form](docs/level_4_fixed_base_arm_only_open_close_evaluation.md)
- [Level 1 Clean-Grasp Report](docs/level_1_handle_grasp_report.md)
- [Level 2 Handle-Follow Report](docs/level_2_handle_follow_open_90_report.md)
- [Level 2 RoboDojo-Style Evaluation](docs/level_2_handle_follow_open_90_evaluation.md)
