# Week 10: Multi-stage Scene Generalization

Full report: [Four-Scene Robot Manipulation Task and Validation Report](FOUR_SCENE_TASK_REPORT.md)

Week10 adds the two harder final demonstration scenes. It imports the Week9
runner and task-system extension rather than copying them.

## Difficulty progression

| Order | Scene | Level 1 | Level 2 | Level 3 (accepted result) |
| --- | --- | --- | --- | --- |
| 3 | File cabinet | navigate and align | grasp and pull drawer | pull, hold, push back, release, retreat |
| 4 | Dishwasher | open the door | switch targets and pull the rack | open door, pull/push rack, regrasp door, close and restore |

The file cabinet increases the prismatic travel and synchronizes the mobile
base with the drawer. The dishwasher combines one horizontal hinge and one
slide joint, two targets, two release/regrasp transitions, target-dependent
approach directions, and full restoration.

## Accepted results

| Task | States | Actions | Target motion | Overlap | Lost grasp | Max arm step |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| File drawer | 368 | 11 | `0.00 -> 0.26 -> 0.00 m` | 0 | 0 | 0.02972 rad |
| Dishwasher | 942 | 24 | door `0.00 -> 0.65 -> 0.00 rad`; rack `0.00 -> 0.24 -> 0.00 m` | 0 | 0 | 0.12038 rad |

Both runs have zero forbidden target contacts and finish with every evaluated
object joint at zero and the gripper open.

The dishwasher's second door grasp deliberately uses an overhead approach.
Once the door is open, its local frame rotates and the original frontal route
would intersect the door panel; the alternate route is selected in the YAML
without changing the generic runner.

## Outputs

- File drawer: [front](assets/file_drawer_open_close.gif),
  [top](assets/file_drawer_open_close_top_view.gif), and
  [summary](results/file_drawer_open_close_summary.json)
- Dishwasher: [front](assets/dishwasher_door_rack_restore.gif),
  [top](assets/dishwasher_door_rack_restore_top_view.gif), and
  [summary](results/dishwasher_door_rack_restore_summary.json)

## Reproduce

From the projects directory:

```bash
scenesmith/.mujoco_venv/bin/python -m week10_note.scripts.run_articulated_task \
  --config week10_note/configs/file_drawer_open_close.yaml

scenesmith/.mujoco_venv/bin/python -m week10_note.scripts.run_articulated_task \
  --config week10_note/configs/dishwasher_door_rack_restore.yaml
```

Add `--skip-render` for a faster numerical-only check.

## Source references

- File-drawer articulation:
  `articraft/data/cache/record_materialization/rec_create-a-simple-openable-drawer-as-an-articulate_20260622_090516_601626_1de2d64e/model.urdf`
- Dishwasher articulation:
  `articraft/data/cache/record_materialization/rec_create-a-complex-articulated-dishwasher-as-an-ar_20260622_101600_814705_5eac46ef/model.urdf`

## Scope boundary

These results validate reusable kinematic task generation and collision-aware
trajectory checking. They do not claim force control, actuator dynamics,
camera-based perception, or a learned policy.
