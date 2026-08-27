# 07. From a Fixed Script to a Reusable Task System

## 1. What Generalization Means

Generalization does not mean that the program suddenly understands any natural-language request. It means that stable operations become reusable modules.

Instead of copying the gripper loop, a task calls `change_gripper(...)`. Instead of copying base interpolation, it calls `move_base(...)`. A new task primarily specifies action order, targets, and parameters.

Python defines how actions work. YAML defines what actions to perform.

## 2. What Should Stay in Python

- interpolation algorithms;
- MuJoCo state application;
- IK solving;
- collision and contact checks;
- success-check implementations;
- trajectory and video output.

## 3. What Should Move to Configuration

- target handle and object joint names;
- robot work positions;
- target angle;
- action order;
- sample counts and step limits;
- permitted and forbidden contacts.

The executor follows this pattern:

```text
read YAML
-> get the next action name
-> find its Python function in the action registry
-> pass target and numeric parameters
-> receive generated states
-> continue with the next action
```

## 4. Problem with the Fixed Level 5 Script

Although Level 5 reused some right-door work, the main script still hard-coded:

- left and right handle names;
- left and right hinge names;
- base work poses;
- phase order;
- opening angle;
- samples per phase.

A new task therefore required editing the Python flow.

## 5. Desired YAML Form

```yaml
task_name: open_both_cabinet_doors

actions:
  - action: move_base
    target: right_door_station

  - action: grasp_target
    target: right_handle

  - action: follow_hinge_joint
    joint: right_hinge
    angle_deg: 90

  - action: change_gripper
    target: open

  - action: move_base
    target: left_door_station

  - action: grasp_target
    target: left_handle

  - action: follow_hinge_joint
    joint: left_hinge
    angle_deg: 90
```

The executor reads the same structure for different targets.

## 6. Reusable Components to Extract

### Generic State

Replace fixed fields such as `left_hinge` and `right_hinge` with:

```python
object_joints: dict[str, float]
```

This dictionary can hold any number of named cabinet, door, drawer, or microwave joints.

### Action Primitives

```python
hold_pose()
move_base()
move_arm()
change_gripper()
grasp_target()
follow_hinge_joint()
```

### Generic Validation

```python
check_joint_goal()
check_gripper_distance()
check_required_contacts()
check_forbidden_contacts()
check_environment_overlap()
check_motion_continuity()
```

## 7. Recommended Structure

```text
task_system/
  state.py          reusable state format
  primitives.py     basic actions
  executor.py       ordered action dispatch
  targets.py        scene targets and work poses
  validators.py     collision and success checks
  configs/
    level_5.yaml
```

## 8. Safe Refactoring Order

1. Keep the stable Level 5 script as a reference.
2. Create reusable state and action modules separately.
3. Re-express Level 5 through configuration.
4. Compare old and new trajectories and measurements.
5. Confirm both doors still reach 90 degrees.
6. Confirm all 93 environment geoms still produce zero forbidden overlap.
7. Only then use the framework for a new task.

The first useful primitives are `hold_pose`, `move_base`, and `change_gripper`. More complex IK actions are added after the basic state pipeline is stable.

## 9. How to Recognize Real Reuse

Without editing executor code, configuration should support:

- opening only the left door;
- opening only the right door;
- opening right then left;
- opening and then closing;
- changing the target from 90 to 45 degrees;
- replacing the target with another hinged object.

If every target requires a copied task script, generalization has not been achieved.

## 10. Self-Check

1. What belongs in Python and what belongs in YAML?
2. Why is `object_joints` more reusable than two fixed hinge fields?
3. Why retain the stable Level 5 implementation?
4. Which simple primitives should be extracted first?

Answers: Python implements actions while YAML composes them; a dictionary supports arbitrary joint names; the stable script provides regression evidence; begin with hold, base motion, and gripper change.
