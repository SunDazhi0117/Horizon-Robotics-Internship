# 02. Task Sequences and States

## 1. A Task Is More Than One Sentence

"Open both cabinet doors" is a human instruction. Code needs a detailed sequence:

```text
base pose + arm pose + gripper opening + door angles
-> one complete frame
many ordered frames
-> one task trajectory
```

## 2. Purpose of append_state

Source: `run_level_5_sequential_open_both_doors.py:569-589`

```python
def append_state(
    sequence,
    phase,
    base,
    qpos,
    finger,
    left_hinge,
    right_hinge,
    active_handle=None,
):
    sequence.append(
        {
            "phase": str(phase),
            "base": np.asarray(base, dtype=float).copy(),
            "qpos": np.asarray(qpos, dtype=float).copy(),
            "finger": float(finger),
            "left_hinge": float(left_hinge),
            "right_hinge": float(right_hinge),
            "active_handle": active_handle,
        }
    )
```

The function converts every input into a predictable type and appends one independent state dictionary. Copies prevent a later array edit from silently changing older frames.

## 3. Meaning of Each Field

### sequence

The ordered list that stores the complete trajectory.

### phase

A readable stage label such as:

```python
"grasp_right_handle"
"open_left_door"
```

It supports debugging and phase-specific validation.

### base

Usually `[x, y, yaw]`: planar position and heading of the mobile base.

### qpos

The Panda arm configuration. It contains seven joint angles, not one Cartesian hand position.

### finger

The gripper opening. Larger values open the fingers; smaller values close them.

### left_hinge and right_hinge

The two cabinet-door angles in radians.

### active_handle

Identifies the handle currently being manipulated. It is `None` during navigation or retreat.

## 4. How the Grasp Loop Works

```python
for alpha in np.linspace(0.0, 1.0, 17)[1:]:
    append_state(
        sequence,
        "grasp_left_handle",
        LEFT_WORK_BASE,
        left_start,
        (1.0 - alpha) * OPEN_FINGER + alpha * GRASP_FINGER,
        0.0,
        TARGET_ANGLE,
        LEFT_HANDLE,
    )
```

Step by step:

1. `np.linspace` creates 17 values from 0 to 1.
2. `[1:]` skips the first value because the initial open state already exists.
3. The base and arm stay fixed.
4. The finger value blends from `OPEN_FINGER` to `GRASP_FINGER`.
5. The left door remains closed at `0.0`.
6. The right door remains at `TARGET_ANGLE`.
7. The active target is `LEFT_HANDLE`.

At `alpha = 0`, the expression equals `OPEN_FINGER`. At `alpha = 1`, it equals `GRASP_FINGER`.

## 5. Why the Original State Was Not Fully General

Fields named `left_hinge` and `right_hinge` only fit one double-door cabinet. A reusable state should instead store arbitrary object joints:

```python
object_joints = {
    "cabinet_left_hinge": 0.0,
    "cabinet_right_hinge": 1.57,
    "microwave_door_hinge": 0.0,
}
```

This became the `TaskState.object_joints` design in the reusable task system.

## 6. Self-Check

1. Why does one task need many states?
2. Why are arrays copied inside `append_state`?
3. Which field tells validation what the robot is grasping?
4. In the grasp loop, which value changes and which values remain fixed?

Answers: motion is continuous; copies preserve history; `active_handle` identifies the target; the finger opening changes while base, arm, and door angles remain fixed.
