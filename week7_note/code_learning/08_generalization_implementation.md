# 08. First Reusable Task-System Implementation

The first reusable implementation was created beside the stable Level 5 code. It did not modify the accepted Level 5 task.

## 1. File Structure

```text
task_system/
  state.py
  primitives.py
  executor.py
  run_config.py
  mujoco_adapter.py
  mujoco_manipulation.py
  panda_validation.py
  run_level5_reusable_demo.py
  configs/
    foundation_demo.yaml
    parameter_change_demo.yaml
    level5_reusable_left_door.yaml

tests/
  test_task_system.py
```

## 2. TaskState

File: [state.py](../task_system/state.py)

`TaskState` stores one complete frame:

```text
phase
base
arm_qpos
gripper
object_joints
active_target
```

`object_joints` is a dictionary:

```python
{
    "cabinet_left_hinge": 0.0,
    "cabinet_right_hinge": 1.57,
    "microwave_door_hinge": 0.0,
}
```

The state is no longer limited to two cabinet doors.

`TaskState` is treated as immutable. An action creates an updated state with `with_updates` instead of modifying the old state. This preserves the complete history:

```text
state_0: before action
state_1: small motion
state_2: continued motion
state_3: action complete
```

## 3. Reusable Primitives

File: [primitives.py](../task_system/primitives.py)

### hold_pose

Repeats the current state for a configured number of frames.

### move_base

Starts from the current base pose, visits configured waypoints, and returns a smooth base-state sequence.

### move_arm

Connects one or more arm-joint goals while enforcing a maximum adjacent joint step.

### change_gripper

Interpolates from the current gripper opening to a target opening and can set or clear `active_target`.

Each primitive accepts a state plus parameters and returns new states. It does not know the full task.

## 4. Action Registry

File: [executor.py](../task_system/executor.py)

The executor stores a mapping:

```text
hold_pose      -> hold_pose function
move_base      -> move_base function
move_arm       -> move_arm function
change_gripper -> change_gripper function
```

When YAML contains `action: move_base`, the executor looks up and calls that function. Unknown actions fail immediately and list available names.

## 5. YAML Configuration

File: [foundation_demo.yaml](../task_system/configs/foundation_demo.yaml)

The configuration has:

```text
initial_state: starting values
actions: ordered operation list
```

The demonstration holds the initial state, moves the base, moves the arm, and closes the gripper. YAML stores targets and parameters; Python stores interpolation formulas.

## 6. Executor Workflow

```text
read initial_state
-> create TaskState
-> read first action
-> find the registered primitive
-> generate new states
-> use the final state as the next action's start
-> continue until actions are exhausted
```

The result records which state indices belong to each action, making collision or task failure easier to locate.

## 7. Foundation Test Result

Tests cover:

- defensive copying of input arrays;
- state immutability;
- arbitrary object-joint dictionaries;
- base interpolation reaching its goal;
- arm interpolation respecting `max_step`;
- gripper target assignment and clearing;
- YAML composition of four actions;
- rejection of unknown actions.

Recorded result:

```text
14 tests passed
4 actions
18 generated states
```

## 8. MuJoCo Integration

The next layer adds:

- `MujocoStateAdapter` to write `TaskState` into real `MjData`;
- state read-back and round-trip error checks;
- `PandaStateValidator` for environment overlap and handle contact;
- conversion of the saved 429-state Level 5 trajectory into `TaskState`;
- regression checks against 93 environment geoms.

Recorded full regression result:

```text
passed = true
states = 429
environment geoms = 93
environment overlap failures = 0
forbidden target contact failures = 0
base roundtrip error = 0
arm roundtrip error = 0
object joint roundtrip error = 0
```

## 9. Reusable Manipulation Actions

The second layer implements two real MuJoCo actions:

- `grasp_target`: solve IK from a target-relative pose and close the gripper;
- `follow_hinge_joint`: change a hinge angle, resolve IK at each state, and keep the hand following the door.

Every generated state checks environment overlap and forbidden contact. Hinge following also requires both fingers to retain target contact.

The independent YAML demonstration regenerated the left-handle grasp and 90-degree left-door opening:

```text
actions = 2
states = 82
final left hinge = 1.5707963267948966 rad
environment overlap failures = 0
forbidden target contact failures = 0
result = PASS
```

This proves that YAML can call real IK and hinge-follow actions to generate a new MuJoCo trajectory; it is not merely replaying saved states.

## 10. Remaining Work at This Stage

- discover handles and owning joints from scene structure;
- support slide joints for drawers and microwave trays;
- generate the complete navigation and two-door Level 5 task from YAML;
- advance from qpos kinematics to actuator-driven `data.ctrl + mj_step` execution.

These limitations became the starting point for the Week 8 target-discovery and position-generalization work.
