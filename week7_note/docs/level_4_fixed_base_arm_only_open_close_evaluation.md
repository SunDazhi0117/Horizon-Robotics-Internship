# Level 4 Fixed-Base Cabinet Open-Close Evaluation

## Conclusion

Level 4 scored `100/100` in one local deterministic evaluation, with an overall result of `PASS`.

This score only means that the current MuJoCo scene, fixed initial state, and scripted trajectory passed our task thresholds. It is not an official RoboDojo score.

## Task Definition

| Field | Value |
| --- | --- |
| Task name | Fixed-Base Open and Close Cabinet Door |
| Instruction | Keep the mobile base fixed, retain the right-door handle grasp, open the door to 90 degrees, and close it again. |
| Platform | MuJoCo local simulation |
| Category | Long-Horizon (primary) / Precision (secondary) |
| Data source | Validated scripted arm-only kinematic trajectory |
| Initial state | Base fixed; both fingers securely hold the closed door handle |
| Goal state | Door reaches at least 85 degrees and finishes within 5 degrees of closed; all grasp, collision, and penetration checks pass |

## Scoring

| Score | Condition |
| --- | --- |
| 0 | The door does not reach 85 degrees, does not return within 5 degrees of closed, the base moves, grasp is lost, or a forbidden collision/penetration occurs. |
| 100 | The base remains fixed, both fingers retain handle contact, the door opens and closes, and every safety threshold passes. |

## Evaluation Form

| Check | Threshold | Measured value | Result |
| --- | --- | --- | --- |
| Door opens successfully | `>= 85 degrees` | `90 degrees` | PASS |
| Door closes successfully | `<= 5 degrees` | `0 degrees` | PASS |
| Base remains fixed | drift `<= 1e-9` | `0.0` | PASS |
| Two-finger handle contact | minimum contacts `>= 2` | `2` | PASS |
| Hand remains near handle | distance `<= 0.06 m` | `0.0532051 m` | PASS |
| Continuous arm trajectory | joint step `<= 0.20 rad` | `0.1113531 rad` | PASS |
| Cabinet visual penetration | failures `= 0` | `0` | PASS |
| Non-finger handle contact | failures `= 0` | `0` | PASS |
| Arm/door-panel collision | failures `= 0` | `0` | PASS |

Validated states: `149`.

Local single-run score: `100/100`.

## Capability Coverage

| Dimension | Level 4 status |
| --- | --- |
| Precision | Passed in a fixed scene and initial state |
| Long-Horizon | Covers grasp retention, opening, holding, and closing |
| Generalization | Not evaluated |
| Memory | Not evaluated |
| Open-vocabulary | Not evaluated |

## Current Limitations

1. Execution directly sets joint states and is a scripted kinematic trajectory.
2. Dynamic closed-loop control with `data.ctrl + mj_step` has not been implemented.
3. Robot, cabinet, handle, and initial-angle randomization has not been evaluated.
4. Only one deterministic run was evaluated; no multi-rollout success rate is available.
5. This is not an official RoboDojo benchmark result.

## Evidence

- Main view: `assets/videos/level_4_fixed_base_arm_only_open_close.gif`
- Top view: `assets/videos/level_4_fixed_base_arm_only_open_close_top_view.gif`
- Summary: `assets/results/level_4_fixed_base_arm_only_open_close_summary.json`
- Evaluation JSON: `assets/results/level_4_fixed_base_arm_only_open_close_evaluation.json`
- Trajectory: `assets/results/level_4_fixed_base_arm_only_open_close_trajectory.json`
