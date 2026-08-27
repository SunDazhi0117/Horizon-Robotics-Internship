# Case 03 - Clean Sliding Drawer with Storage Area

## 1. Object Name

Clean Sliding Drawer with Storage Area

The object name in the code is:

```python
model = ArticulatedObject(name="clean_sliding_drawer")
```

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and the `gpt-5.5` model.

The goal was to generate a simple drawer that is not a solid block, but has a visible storage area.

## 3. Object Structure

This object contains two main parts:

1. `cabinet`
2. `drawer`

The `cabinet` is the fixed parent part.

The `drawer` is the movable child part.

This matches the real structure of a drawer: the cabinet stays fixed, while the drawer slides in and out.

## 4. Cabinet Part

The `cabinet` is built from several simple box-shaped visual elements:

* `side_panel_0`
* `side_panel_1`
* `bottom_rail`
* `top_rail`
* `rear_panel`
* `runner_0`
* `runner_1`

The runners are especially important because they provide support for the drawer. This helps prevent the drawer from becoming a floating or disconnected part.

## 5. Drawer Part

The `drawer` is built from separate box panels:

* `bottom_panel`
* `side_wall_0`
* `side_wall_1`
* `back_wall`
* `front_panel`
* `handle_post_0`
* `handle_post_1`
* `handle_bar`

The drawer is not a solid block. It is built like an open-top tray.

There is no `top_panel`, so the drawer has a visible storage cavity.

This is the main improvement compared with the previous drawer V1.

## 6. Joint / Articulation

The key articulation is:

```python
model.articulation(
    "cabinet_to_drawer",
    ArticulationType.PRISMATIC,
    parent=cabinet,
    child=drawer,
    origin=Origin(xyz=(0.0, 0.0, 0.12)),
    axis=(1.0, 0.0, 0.0),
    motion_limits=MotionLimits(effort=35.0, velocity=0.35, lower=0.0, upper=0.20),
)
```

My understanding:

* The joint name is `cabinet_to_drawer`.
* The joint type is `PRISMATIC`.
* The parent part is `cabinet`.
* The child part is `drawer`.
* The axis is `(1.0, 0.0, 0.0)`.
* The motion limit is from `0.0` to `0.20`.

This means the drawer slides outward along the X axis.

The `cabinet` stays fixed, and the `drawer` moves in a straight line.

## 7. Motion Behavior

In the Viewer, the drawer slides outward from the cabinet.

The motion is linear, which is appropriate for a drawer.

Compared with Drawer V1, this version looks cleaner because the drawer front does not obviously intersect with the cabinet frame.

## 8. Storage Area

This version successfully creates a visible storage area.

The storage area is created by using separate panels:

```python
bottom_panel
side_wall_0
side_wall_1
back_wall
front_panel
```

Because there is no `top_panel`, the drawer remains open at the top.

This makes it look like a real drawer that can store objects.

## 9. Tests / Validation

The `run_tests()` function checks several important conditions:

1. The `cabinet` is the fixed root.
2. The `drawer` is the movable child.
3. The joint type is `PRISMATIC`.
4. The drawer has reasonable sliding limits.
5. The drawer moves outward along the intended axis.
6. The drawer front clears the side panels.
7. The drawer front clears the top rail and bottom rail.
8. The drawer rests on the cabinet runner.
9. The drawer tray is built from separate box panels.
10. The drawer has an open storage cavity.

The most important storage check is:

```python
ctx.check(
    "drawer has an open storage cavity",
    side_top > bottom_top + 0.09 and "top_panel" not in drawer_visual_names,
)
```

This test checks that the side walls are higher than the bottom panel and that the drawer does not have a top panel.

Therefore, the drawer has an open storage cavity.

## 10. Why This Version Is Better Than Drawer V1

Drawer V1 had a visible interpenetration problem. The drawer front appeared to overlap with the cabinet frame in the Viewer.

This version is better because:

1. The drawer is made from separate panels instead of one solid block.
2. The drawer front has clearance from the cabinet frame.
3. The tests check gaps between the drawer front and the cabinet rails.
4. The runners support the drawer and help avoid floating geometry.
5. The storage area is explicitly checked by the validation tests.

## 11. Current Limitation

This version mainly uses visual geometry.

I did not clearly see separate collision geometry definitions.

Therefore, the object looks good in the Viewer and has correct articulated motion, but its physical simulation quality may still need further checking.

## 12. Status

This is a successful case.

It satisfies the main requirements:

* fixed cabinet
* movable drawer
* `PRISMATIC` joint
* straight sliding motion
* visible storage area
* clean visual structure
* no obvious interpenetration in the Viewer

## 13. One-Sentence Summary

This object is a successful articulated drawer because it has a fixed `cabinet`, a movable `drawer`, a `PRISMATIC` sliding joint, and an open-top storage area built from separate box panels.
