# 03. Interpolation and Continuous Motion

## 1. Key Poses and Intermediate Frames

Humans usually define only a few important poses:

```text
A: arm folded
B: arm beside the cabinet
C: gripper on the handle
```

Rendering and collision validation also need the states between A, B, and C. Interpolation creates these intermediate frames.

Jumping directly from A to B can hide a collision because the start and end may be safe while the path between them crosses furniture.

## 2. Arm-Joint Interpolation

Source: `run_level_5_sequential_open_both_doors.py:538-552`

```python
def interpolate_joint_path(
    path: list[np.ndarray],
    max_step: float = 0.045,
) -> list[np.ndarray]:
    dense: list[np.ndarray] = [path[0].copy()]
    for start, end in zip(path[:-1], path[1:]):
        count = max(
            2,
            int(np.ceil(np.max(np.abs(end - start)) / max_step)) + 1,
        )
        dense.extend(
            (1.0 - alpha) * start + alpha * end
            for alpha in np.linspace(0.0, 1.0, count)[1:]
        )
    return dense
```

### Pairing Edges

For `path = [A, B, C]`:

```text
path[:-1] -> [A, B]
path[1:]  -> [B, C]
zip(...)  -> (A, B), (B, C)
```

The loop handles one edge at a time.

### Selecting the Number of Samples

`end - start` computes the change of every arm joint. `np.abs` ignores direction, `np.max` finds the largest joint change, and division by `max_step` estimates how many intervals are needed. `np.ceil` rounds upward so no step exceeds the requested limit.

A smaller `max_step` creates more states, denser collision checks, smoother video, and longer execution time.

### Linear Interpolation

```python
(1.0 - alpha) * start + alpha * end
```

- `alpha = 0.0`: start pose
- `alpha = 0.5`: midpoint
- `alpha = 1.0`: end pose

## 3. Base-Path Interpolation

Source: `run_level_5_sequential_open_both_doors.py:555-566`

```python
def interpolate_base_path(
    waypoints: tuple[np.ndarray, ...],
    steps_per_edge: int = 31,
) -> list[np.ndarray]:
    dense: list[np.ndarray] = [waypoints[0].copy()]
    for start, end in zip(waypoints[:-1], waypoints[1:]):
        dense.extend(
            (1.0 - smooth(float(alpha))) * start
            + smooth(float(alpha)) * end
            for alpha in np.linspace(0.0, 1.0, steps_per_edge)[1:]
        )
    return dense
```

`tuple[np.ndarray, ...]` means a tuple containing any number of NumPy arrays. `steps_per_edge=31` is a default argument; callers can replace it.

Waypoints can force a safer route:

```python
waypoints = (
    START_BASE,
    STAGING_BASE,
    PREAPPROACH_BASE,
    WORK_BASE,
)
```

The robot travels through every point instead of taking one direct line.

## 4. Why smooth Is Used

Linear interpolation starts and stops at a constant mathematical rate with abrupt velocity changes at segment boundaries. A smooth-step function changes slowly near 0 and 1 and more quickly in the middle. This improves visual and joint continuity.

Smoothing does not avoid obstacles. It changes timing along the same geometric path.

## 5. Interpolation Does Not Guarantee Safety

```text
safe pose A
-> straight interpolation through a cabinet
-> safe pose B
```

Both endpoints can pass while intermediate states fail. The correct workflow is:

```text
choose safe waypoints
-> generate dense interpolation
-> validate every state
-> redesign waypoints when validation fails
```

This is why Level 5 introduced `LEFT_STAGING_BASE` and `LEFT_PREAPPROACH_BASE`.

## 6. Numerical Example

For `start = [0, 0]`, `end = [2, 4]`, and `alpha = 0.25`:

```text
0.75 * [0, 0] + 0.25 * [2, 4] = [0.5, 1.0]
```

The same formula works for a two-value point, a three-value base pose, or seven arm joints.

## 7. Self-Check

1. What are the input and output of interpolation?
2. What happens to state count when `max_step` decreases?
3. Does smooth motion guarantee no collision?
4. Why use intermediate waypoints?

Answers: sparse key poses become dense states; state count increases; smoothness does not guarantee safety; waypoints route motion through selected safer regions.
