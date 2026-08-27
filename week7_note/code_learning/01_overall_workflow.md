# 01. Complete Level 5 Code Workflow

## 1. One-Sentence Overview

The task script builds a MuJoCo model, generates a frame-by-frame robot trajectory, validates every frame, renders selected frames, and writes PASS/FAIL evidence.

```text
XML scene
-> MjModel and MjData
-> key poses and interpolated trajectories
-> sequence of task states
-> apply one state at a time
-> collision, contact, and continuity checks
-> summary, evaluation, and videos
```

## 2. Load the MuJoCo Model

Source: `run_level_5_sequential_open_both_doors.py:602-607`

```python
model = mujoco.MjModel.from_xml_path(str(TASK_XML))
data = mujoco.MjData(model)
```

`model` stores fixed structure: bodies, joints, geoms, actuator definitions, limits, masses, and timestep. `data` stores changing state: time, qpos, qvel, contacts, and control input.

Think of `model` as the world specification and `data` as the current frame of that world.

## 3. Compute Feasible Poses and Paths

The script obtains named IDs, reads handle and hinge poses, and solves arm IK for important poses. A function may return several values:

```python
left_start, left_open, left_handle = build_left_door_path(model, data)
```

Python assigns the three returned values to three variables in order.

These values describe what the robot should do geometrically; they do not yet move simulation time.

## 4. Build the Task Sequence

```python
sequence: list[dict[str, object]] = []
```

This empty list becomes the task script. Every call to `append_state()` adds one complete frame containing:

- phase name;
- base pose;
- seven arm-joint values;
- gripper opening;
- left and right door angles;
- active handle.

The action chain is conceptually:

```text
start
-> move to right door
-> grasp right handle
-> open right door
-> release and retreat
-> move around cabinet
-> grasp left handle
-> open left door
-> finish
```

## 5. Apply and Validate Every Frame

Source: `run_level_5_sequential_open_both_doors.py:755-778`

```python
for index, state in enumerate(sequence):
    apply_state(model, data, state)
    check = validate_state(model, data, state)
    checks.append(check)
```

For every iteration:

1. `index` identifies the current frame.
2. `state` contains the desired values for that frame.
3. `apply_state` writes those values into `data.qpos`.
4. `mj_forward` recomputes body and geom poses.
5. `validate_state` checks overlap, contact, grasp retention, and continuity.
6. The result is appended to `checks`.

This is why the task can identify the exact phase and frame where a failure appears.

## 6. Produce PASS or FAIL

The final result combines multiple conditions. A typical structure is:

```python
passed = all(
    [
        right_door_reached_target,
        left_door_reached_target,
        grasp_checks_passed,
        collision_failures == 0,
        joint_step_within_limit,
    ]
)
```

`all(...)` returns `True` only when every condition is true. A visually convincing video is not enough; the numerical checks must also pass.

## 7. Nature of the Current Method

The current Level 5 system is:

- a scripted kinematic trajectory;
- generated partly through interpolation and IK;
- validated through MuJoCo geometry and contact state;
- deterministic for the recorded initial scene.

It is not:

- a reinforcement-learning policy;
- autonomous task planning;
- dynamic closed-loop control with actuator feedback;
- an official RoboDojo benchmark result.

## 8. Self-Check

1. Why are both `model` and `data` required?
2. What does the empty `sequence` eventually contain?
3. What does arm `qpos` represent in one state?
4. What extra value does `enumerate` provide?

Answers: `model` stores fixed structure while `data` stores current state; `sequence` stores time-ordered task frames; arm qpos stores current joint angles; `enumerate` adds the frame index.
