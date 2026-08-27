# Level 2 RoboDojo-Style Evaluation

## Conclusion

Level 2 scored `100/100` in our RoboDojo-style single deterministic evaluation. Its official RoboDojo score remains `N/A`.

These statements do not conflict. `100/100` means that the MuJoCo trajectory completed the local cabinet task and passed every local safety threshold. `N/A` means that it was not evaluated in RoboDojo's official Isaac Sim environment and was not completed by a closed-loop policy using visual observations.

## Task Definition

| Field | Value |
| --- | --- |
| Task name | Open Cabinet Door to 90 Degrees |
| Instruction | Move to the cabinet, grasp the right-door handle, and open the cabinet door to 90 degrees. |
| Description | Move the Panda to the cabinet, place the two fingers around the right-door handle, and follow the handle until the door reaches 90 degrees. |
| Platform | MuJoCo local simulation |
| Category | Precision (primary) / Long-Horizon (secondary) |
| Data Source | Scripted inverse-kinematics trajectory |
| Usage | Local deterministic evaluation only |

## Adapted Scoring

Following the binary scoring style on the RoboDojo simulation-task page, this task uses:

| Score | Condition |
| --- | --- |
| 0 | The door does not reach 85 degrees, the grasp is lost, or a forbidden handle/door collision or penetration occurs. |
| 100 | The door opens at least 85 degrees, both fingers retain handle contact, the hand follows the handle, and all collision and visual-overlap thresholds pass. |

## Level 2 Result

| Check | Result | Evidence |
| --- | --- | --- |
| Door reaches target angle | PASS | Final `1.570796 rad = 90 degrees` |
| Two-finger contact retained | PASS | Minimum independent finger contacts over 49 opening samples: `2` |
| Hand follows handle | PASS | Maximum hand-center-to-handle distance `0.053205 m`, below the `0.06 m` limit |
| Hand-pose tracking | PASS | Maximum position error `1.49e-7 m`; maximum rotation error `7.27e-7 rad` |
| Visual overlap | PASS | Failure events: `0` |
| Non-finger handle contact | PASS | Failure events: `0` |
| Arm/door collision | PASS | Door-panel collision failures: `0` |

Local single-run task score: `100/100`.

## Five Capability Dimensions

The official RoboDojo simulation benchmark evaluates Generalization, Memory, Precision, Long-Horizon behavior, and Open-vocabulary instruction following.

| Dimension | Level 2 status |
| --- | --- |
| Precision | Passed in one fixed scene and initial state |
| Long-Horizon | Partially covered through approach, grasp, and opening stages |
| Generalization | Not evaluated; robot, cabinet, handle, and initial pose were fixed |
| Memory | Not evaluated; no hidden state or instruction history was required |
| Open-vocabulary | Not evaluated; no language model or policy parsed natural language |

## Why This Is Not an Official RoboDojo Score

1. RoboDojo's official task set does not contain this exact mobile-Panda cabinet-opening task.
2. Official RoboDojo simulation evaluation uses Isaac Sim; this result uses MuJoCo.
3. Level 2 sets robot state from a precomputed IK trajectory instead of using a policy that maps camera and proprioceptive observations to actions.
4. Only one execution from one fixed initial state was evaluated; no randomized multi-rollout success rate was measured.
5. The checks cover kinematic states, contacts, and overlaps rather than full dynamic control stability.

Accurate statement:

`Level 2 passed a RoboDojo-style local deterministic task evaluation with 100/100.`

Inaccurate statement:

`Level 2 achieved 100 on the official RoboDojo benchmark.`

## Next Evaluation Upgrade

The next evaluation should preserve the task but advance beyond checking one deterministic trajectory:

1. Execute with `data.ctrl + mj_step` instead of directly setting `qpos`.
2. Run at least 20 rollouts and report success rate.
3. Randomize the robot initial pose, door angle, and handle pose.
4. Report standard-scene and randomized-scene success rates separately.
5. Then consider moving the task to Isaac Sim or integrating a real observation-to-action policy.

## References

- RoboDojo simulation tasks: https://robodojo-benchmark.com/doc/sim-tasks/
- RoboDojo overview: https://robodojo-benchmark.com/
- RoboDojo usage: https://robodojo-benchmark.com/doc/usage/
