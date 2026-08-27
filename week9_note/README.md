# Week 9: Single-joint Scene Generalization

Week9 adds the first two of four final demonstration scenes. Both reuse the
mobile Panda, target-relative navigation, staged Cartesian approach, grasp IK,
collision checking, task-state executor, YAML configuration, and fixed-camera
rendering built in Week6-Week8.

The scene geometry follows articulated structures already materialized by the
local Articraft project. The runtime uses lightweight MuJoCo primitives so the
collision geometry, target handle, and joint limits remain explicit and easy
to validate.

## Difficulty progression

| Order | Scene | Level 1 | Level 2 | Level 3 (accepted result) |
| --- | --- | --- | --- | --- |
| 1 | Sliding window | navigate and align | grasp and slide open | open, hold, close, release, retreat |
| 2 | Storage box | navigate and grasp | lift the horizontal lid | open, hold, close, release, retreat |

The accepted YAML is the complete Level 3 task. Earlier levels are prefixes of
the same action sequence, so the progression does not require separate task
implementations.

## Accepted results

| Task | States | Target motion | Overlap | Lost grasp | Max arm step |
| --- | ---: | --- | ---: | ---: | ---: |
| Sliding window | 361 | `0.00 -> 0.28 -> 0.00 m` | 0 | 0 | 0.02972 rad |
| Storage box | 385 | `0.00 -> 0.55 -> 0.00 rad` | 0 | 0 | 0.03693 rad |

Both runs also have zero forbidden target contacts and finish with the gripper
open and the object restored to its initial state.

## Outputs

- Sliding window: [front](assets/sliding_window_open_close.gif),
  [top](assets/sliding_window_open_close_top_view.gif), and
  [summary](results/sliding_window_open_close_summary.json)
- Storage box: [front](assets/storage_box_open_close.gif),
  [top](assets/storage_box_open_close_top_view.gif), and
  [summary](results/storage_box_open_close_summary.json)

## Reproduce

From the projects directory:

```bash
scenesmith/.mujoco_venv/bin/python -m week9_note.scripts.run_articulated_task \
  --config week9_note/configs/sliding_window_open_close.yaml

scenesmith/.mujoco_venv/bin/python -m week9_note.scripts.run_articulated_task \
  --config week9_note/configs/storage_box_open_close.yaml
```

Add `--skip-render` for a faster numerical-only check.

## Source references

- Sliding-window articulation:
  `articraft/data/cache/record_materialization/rec_create-a-simple-articulated-horizontal-sliding-w_20260617_060456_270105_b0d95f92/model.urdf`
- Hinged-box articulation:
  `articraft/data/cache/record_materialization/rec_create-a-simple-box-with-an-openable-hinged-lid-_20260622_091129_705529_3df55505/model.urdf`

## Scope boundary

These are validated kinematic demonstrations. They do not claim force control,
camera-based perception, actuator dynamics, or a learned policy.
