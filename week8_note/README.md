# Week 8: Reusing Existing Code for New Tasks

Week8 focuses on task generalization: applying the reusable actions developed
in Week7 to a different articulated object without rewriting a complete task
script.

## Main question

How can an existing robot-task implementation be reused for a new object and
a new task mainly by changing configuration, target names, and parameters?

## Week7 baseline

The reusable foundation remains in `week7_note/task_system/`:

- `TaskState` stores one commanded robot and object state.
- `move_base`, `move_arm`, `change_gripper`, and `hold_pose` build trajectories.
- `grasp_target` solves grasp IK and closes the gripper.
- `follow_hinge_joint` keeps the hand attached while a hinge moves.
- `PandaStateValidator` checks visual overlap and forbidden contact.
- YAML selects actions and parameters.

Stable Week7 code and assets stay in their original locations. Week8 imports
and extends them instead of moving or duplicating them.

## Completed new task

The first generalization target is a microwave door:

    approach the microwave
    -> locate the door handle and hinge
    -> grasp the handle
    -> open the door
    -> hold
    -> close the door
    -> release

The task is now complete. The accepted baseline is expressed by
`configs/microwave_open_hold_close.yaml`. A second target-relative version is
expressed by `configs/microwave_open_hold_close_target_relative.yaml`; it
computes the robot base goal from the live target geom pose instead of storing
an absolute world waypoint. Both versions reuse Week7 actions plus general
Week8 extensions for articulation discovery, target-relative navigation, and
collision-checked target approach.

The accepted run contains 401 states. The microwave door opens from `0.0` to
`1.0 rad`, returns to `0.0 rad`, and then the gripper releases and retreats.
Numerical checks found zero visual-overlap failures, zero forbidden contacts,
and zero grasp-loss failures. Fixed front and top-view videos were also
inspected.

The same framework has now been applied to a second object category: the room
entry door. A separate YAML config reuses the existing navigation, approach,
grasp, hinge-follow, release, and retreat actions. The accepted entry-door run
contains 578 states, opens the door to `1.0 rad`, closes it again, and passes
all overlap, forbidden-contact, and grasp-retention checks.

## Documents

- [Week8 goal and scope](docs/01_week8_goal_and_scope.md)
- [Existing code reuse map](docs/02_existing_code_reuse_map.md)
- [Microwave task plan](docs/03_microwave_task_plan.md)
- [Acceptance criteria](docs/04_acceptance_criteria.md)
- [Implementation and accepted result](docs/05_microwave_generalization_result.md)
- [Position-generalization validation](docs/06_position_generalization_validation.md)
- [Candidate-route fallback validation](docs/07_candidate_route_fallback.md)
- [Automatic candidate generation](docs/08_automatic_candidate_generation.md)
- [Week8 generalization summary report (English)](docs/09_week8_generalization_summary_report.md)
- [Entry-door cross-object generalization](docs/10_entry_door_cross_object_generalization.md)
- [Automatic robot-base hinge orbit](docs/11_automatic_hinge_orbit.md)

## Directory structure

    week8_note/
      assets/       images and videos from accepted Week8 runs
      configs/      task configuration files
      docs/         learning notes and design decisions
      results/      validation reports and generated trajectories
      scripts/      Week8 entry points and genuinely reusable extensions

## Current status

- Week8 structure: completed
- Week7 reusable-action inventory: completed
- Microwave articulation discovery: completed
- Automatic collision-checked pre-grasp: completed
- Microwave open/close execution: completed
- Numerical evaluation and two-view video inspection: completed
- Target-relative base positioning: completed and validated
- Same-Config moved-object end-to-end test: completed and passed
- Blocked preferred stand with automatic candidate-route fallback: completed
  and passed
- Polar-rule candidate and detour generation: completed and passed
- Cross-object reuse on the room entry door: completed and passed
- Automatic base orbit from the live hinge anchor and axis: completed and
  passed

## Important boundary

This result validates reusable kinematic task generation and collision-aware
trajectory checking. It does not yet claim force-controlled grasping, actuator
dynamics, perception from camera images, or a learned robot policy.
