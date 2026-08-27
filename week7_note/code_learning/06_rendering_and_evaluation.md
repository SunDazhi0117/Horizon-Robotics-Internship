# 06. Rendering and Task Evaluation

## 1. Video and Validation Are Separate Paths

The same MuJoCo state enters two different workflows:

```text
data -> Renderer -> image frames -> GIF or MP4
data -> validate_state -> numerical checks -> PASS or FAIL
```

Video supports human inspection. Numerical state and contact data determine formal acceptance. A plausible frame does not prove that distance, contact, or collision thresholds passed.

## 2. Basic Rendering Syntax

```python
with mujoco.Renderer(model) as renderer:
    renderer.update_scene(data)
    pixels = renderer.render()
```

`with` closes the renderer automatically and releases resources after the block. MuJoCo returns a pixel array. `Image.fromarray(pixels)` converts it into a PIL image that can be saved or added to a GIF.

Level 5 records diagonal, top, and right-side views:

```python
frames.append(Image.fromarray(minimal.render(model, data, "diag")))
top_frames.append(Image.fromarray(minimal.render(model, data, "top")))
right_frames.append(Image.fromarray(render_right_side(model, data)))
```

The right-side camera exposed cabinet penetration that was hidden from the first two views. Multiple cameras improve visual inspection but do not replace geometry checks.

## 3. Validate Every State, Render Fewer Frames

The Level 5 sequence contains 429 validated states. Rendering all of them would add time, file size, and many nearly identical frames.

```python
render_stride = max(1, len(sequence) // 180)
```

For 429 states, `429 // 180` is 2, so approximately every second state is rendered. Validation still processes all 429 states.

```text
validation: every state
video: sampled states
```

## 4. Worst-Case Aggregation

The evaluation uses maximum or minimum values across the complete trajectory:

- maximum hand-to-handle distance;
- minimum number of valid finger contacts;
- maximum adjacent joint step;
- total overlap and forbidden-contact failures.

Worst-case values matter because one severe grasp loss or penetration can invalidate a task even when the average looks good.

## 5. Level 5 Pass Condition

Source: `run_level_5_sequential_open_both_doors.py:877-894`

```python
passed = bool(
    final["right_hinge"] >= TARGET_ANGLE - 0.01
    and final["left_hinge"] >= TARGET_ANGLE - 0.01
    and right_max_distance <= 0.06
    and left_max_distance <= 0.06
    and right_min_contacts >= 2
    and left_min_contacts >= 2
    and max_joint_step <= 0.20
    and not overlap_failures
    and not forbidden_contact_failures
)
```

This requires both doors near 90 degrees, retained two-finger contact, continuous arm motion, zero forbidden visual overlap, and zero forbidden handle contact. Additional checks verify that base and door motion occur only in planned phases.

## 6. Summary Versus Evaluation

`summary.json` stores measured values such as final angles, maximum distance, minimum contacts, maximum joint step, overlap count, and state count.

`evaluation.json` compares those measurements with thresholds:

```python
checks = {
    "right_door_opened_at_least_85_deg": right_angle >= threshold,
    "arm_motion_remained_continuous": max_joint_step <= 0.20,
    "no_environment_visual_overlap": overlap_count == 0,
}

success = all(checks.values())
```

`all` returns true only when every check is true.

## 7. Accepted Level 5 Result

- Final angle of both doors: 90 degrees
- Validated states: 429
- Environment geoms checked: 93
- Environment visual-overlap failures: 0
- Local deterministic evaluation: PASS, 100/100

This is an engineering evaluation in a custom MuJoCo scene. It is not an official benchmark score because it uses a scripted trajectory, one deterministic setup, and no official RoboDojo submission.

## 8. Self-Check

1. Does the renderer determine task success?
2. Why can video render fewer states than validation checks?
3. When does `all(checks.values())` return true?
4. Why use minimum contact count instead of average contact count?
5. What is the difference between summary and evaluation files?

Answers: rendering only creates images; every state must be checked but repeated frames can be omitted; all checks must be true; one grasp-loss frame matters; summary stores measurements while evaluation compares them with thresholds.
