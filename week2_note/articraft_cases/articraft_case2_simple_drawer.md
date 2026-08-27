# Case 02 - Simple Drawer V1

## 1. Object Name

Simple Sliding Drawer V1

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and `gpt-5.5` model.

The object successfully passed compilation and was viewable in the Articraft Viewer.

## 3. Object Structure

This object contains two main parts:

1. `cabinet`
2. `drawer`

The `cabinet` is the fixed part.

The `drawer` is the movable part.

## 4. Cabinet Part

The `cabinet` is built from several box-shaped visual elements:

* `bottom_panel`
* `top_panel`
* `side_panel_0`
* `side_panel_1`
* `back_panel`
* `front_top_rail`
* `front_lower_rail`

These elements form a simple cabinet frame.

## 5. Drawer Part

The `drawer` is built from several box-shaped visual elements:

* `drawer_box`
* `drawer_front`
* `front_handle`

The `drawer_box` represents the sliding drawer body.

The `drawer_front` is the visible front panel.

The `front_handle` is the black handle on the drawer front.

## 6. Joint / Articulation

The key articulation is:

```python
model.articulation(
    "cabinet_to_drawer",
    ArticulationType.PRISMATIC,
    parent=cabinet,
    child=drawer,
    origin=Origin(xyz=(0.0, 0.0, 0.0)),
    axis=(0.0, -1.0, 0.0),
    motion_limits=MotionLimits(effort=30.0, velocity=0.35, lower=0.0, upper=0.18),
)
```

My understanding:

* The joint name is `cabinet_to_drawer`.
* The joint type is `PRISMATIC`.
* The parent part is `cabinet`.
* The child part is `drawer`.
* The axis is `(0.0, -1.0, 0.0)`.
* The motion limit is from `0.0` to `0.18`.

This means the drawer slides outward along the negative Y direction.

## 7. Motion Behavior

In the Viewer, the cabinet stays fixed.

The drawer moves outward in a straight line.

This motion is appropriate for a drawer and shows that the prismatic joint works.

## 8. Issue Observed

Although the prismatic joint works, the visual quality is not clean.

When the drawer is pulled out, the drawer front appears to visually intersect with the cabinet frame, especially around the lower front rail and side frame area.

This suggests that the drawer front is too close to or partially overlapping with the cabinet frame.

## 9. Current Status

This object is useful as a learning case, but it should not be treated as a final clean example.

The articulation structure is correct, but the visual geometry needs improvement.

## 10. One-Sentence Summary

This object is a simple articulated drawer because it has a fixed `cabinet` part and a movable `drawer` part connected by a `PRISMATIC` joint, but the first version has visible geometry interpenetration around the drawer front and cabinet frame.
