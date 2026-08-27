# Case 07 - Horizontal Sliding Window

## 1. Object Name

Horizontal Sliding Window

The generated object name is:

```python
model = ArticulatedObject(name="horizontal_sliding_window")
```

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and the `gpt-5.5` model.

The goal was to create a simple articulated window with:

* one fixed window frame;
* one fixed glass pane;
* one horizontally sliding glass pane;
* separate front and rear tracks.

This case focuses on a horizontal `PRISMATIC` joint.

## 3. Object Structure

The model contains three parts:

1. `frame`
2. `fixed_pane`
3. `sliding_pane`

The structure is:

```text
frame
├── FIXED joint → fixed_pane
└── PRISMATIC joint → sliding_pane
```

The `frame` is the root part.

The `fixed_pane` is connected to the frame using a `FIXED` joint.

The `sliding_pane` is connected to the frame using a `PRISMATIC` joint.

## 4. Window Frame

The frame contains:

* `left_rail`
* `right_rail`
* `top_rail`
* `bottom_rail`
* `front_lower_track`
* `front_upper_track`
* `rear_lower_track`
* `rear_upper_track`

The four main rails form the rectangular window frame.

The front and rear tracks provide two different Y-depth positions for the glass panes.

## 5. Window Dimensions

The main dimensions are:

```python
WINDOW_WIDTH = 1.20
WINDOW_HEIGHT = 0.80
RAIL = 0.06
```

The opening width is:

```python
OPENING_WIDTH = WINDOW_WIDTH - 2.0 * RAIL
```

Therefore:

```text
OPENING_WIDTH = 1.08 metres
```

Each pane uses half of the opening width:

```python
PANE_WIDTH = OPENING_WIDTH / 2.0
```

Therefore:

```text
PANE_WIDTH = 0.54 metres
```

The maximum slide travel is set to one pane width:

```python
SLIDE_TRAVEL = PANE_WIDTH
```

This allows the sliding pane to move from the right half of the window to the left half.

## 6. Fixed Pane

The fixed pane is located on the left half of the window:

```python
FIXED_X = -PANE_WIDTH / 2.0
```

It contains:

* `fixed_glass`
* `fixed_outer_stile`
* `fixed_meeting_stile`

The fixed pane is connected to the frame using:

```python
model.articulation(
    "frame_to_fixed_pane",
    ArticulationType.FIXED,
    parent=frame,
    child=fixed_pane,
    origin=Origin(),
)
```

The `FIXED` articulation prevents the pane from moving relative to the frame.

## 7. Sliding Pane

The sliding pane initially occupies the right half of the window:

```python
SLIDER_CLOSED_X = PANE_WIDTH / 2.0
```

It contains:

* `sliding_glass`
* `sliding_meeting_stile`
* `sliding_outer_stile`
* `sliding_bottom_sash`
* `sliding_top_sash`

The visual geometry is centered on the sliding pane's local coordinate origin.

The joint origin places the complete pane at its closed position.

## 8. Separate Sliding Tracks

The two panes use different Y-depth tracks:

```python
FIXED_TRACK_Y = -0.018
SLIDER_TRACK_Y = 0.018
```

The distance between the two track centers is:

```text
0.036 metres
```

The glass thickness is:

```python
PANE_THICKNESS = 0.012
```

Therefore, the panes are separated in the front-back direction.

When the sliding pane moves in front of or behind the fixed pane, their X-Z projections can overlap without the glass geometry interpenetrating.

This demonstrates the difference between:

```text
Projection overlap: acceptable in this case
Physical interpenetration: not acceptable
```

## 9. Sliding Joint

The sliding articulation is:

```python
model.articulation(
    "frame_to_sliding_pane",
    ArticulationType.PRISMATIC,
    parent=frame,
    child=sliding_pane,
    origin=Origin(
        xyz=(SLIDER_CLOSED_X, SLIDER_TRACK_Y, PANE_Z)
    ),
    axis=(-1.0, 0.0, 0.0),
    motion_limits=MotionLimits(
        effort=20.0,
        velocity=0.4,
        lower=0.0,
        upper=SLIDE_TRAVEL,
    ),
)
```

My understanding:

* joint name: `frame_to_sliding_pane`
* joint type: `PRISMATIC`
* parent: `frame`
* child: `sliding_pane`
* axis: negative X direction
* lower limit: `0.0`
* upper limit: approximately `0.54` metres

The pane therefore slides horizontally from right to left.

## 10. Closed and Open Positions

In the closed position:

```text
fixed pane center   = -0.27 m
sliding pane center = +0.27 m
```

At the maximum slide position:

```text
sliding pane center = +0.27 - 0.54 = -0.27 m
```

Therefore, the sliding pane becomes aligned with the fixed pane in the X direction.

The panes remain separated in the Y direction because they use different tracks.

## 11. Tests and Validation

The generated tests check:

1. The frame is the fixed root.
2. The sliding pane is the movable child.
3. The sliding joint is `PRISMATIC`.
4. The sliding axis is parallel to the X axis.
5. The motion limit corresponds to approximately half of the window opening.
6. The panes use separate Y-depth tracks.
7. The sliding pane remains inside the frame in the closed pose.
8. The sliding pane remains vertically captured by the frame.
9. The sliding pane remains inside the frame in the open pose.
10. The open pane overlaps the fixed pane in X-Z projection.
11. The two panes remain separated in the Y direction.
12. The pane moves only horizontally.

The motion test is:

```python
ctx.check(
    "pane moves horizontally only",
    closed_pos is not None
    and open_pos is not None
    and open_pos[0] < closed_pos[0] - 0.45
    and abs(open_pos[1] - closed_pos[1]) < 1e-6
    and abs(open_pos[2] - closed_pos[2]) < 1e-6,
)
```

This confirms that:

* the X coordinate changes;
* the Y coordinate remains unchanged;
* the Z coordinate remains unchanged.

## 12. Viewer Observation

The object loaded successfully in the Articraft Viewer.

The window frame and fixed pane remained stationary.

The sliding pane moved horizontally along the X direction.

The pane remained within the window frame during movement.

When opened, the sliding pane overlapped the fixed pane in front-view projection while remaining separated in depth.

No obvious severe interpenetration was observed.

## 13. Why This Case Is Useful

Previous `PRISMATIC` examples mainly involved drawers moving along the front-back direction.

This case demonstrates that a `PRISMATIC` joint can also represent horizontal left-right movement.

It also introduces:

* a `FIXED` joint;
* separate depth tracks;
* acceptable projection overlap;
* motion limits derived from object dimensions;
* transparent visual geometry.

## 14. Comparison with Drawer Cases

The drawer and sliding window both use `PRISMATIC` joints, but their movement directions are different.

### Drawer

```text
Movement: front-back
Typical axis: Y axis
```

### Sliding Window

```text
Movement: left-right
Axis: X axis
```

This shows that the same joint type can represent different motions depending on the joint axis.

## 15. Current Limitations

The object mainly uses visual geometry.

Explicit collision geometry is not clearly defined.

The glass is represented by a thin transparent box rather than a physically detailed glass material.

The validation tests check geometry and kinematics, but they do not verify:

* friction;
* contact with the sliding tracks;
* physical support;
* dynamic stability in SAPIEN or MuJoCo.

## 16. Status

This is a successful case.

Successful features include:

* fixed frame;
* fixed glass pane;
* independently sliding pane;
* horizontal `PRISMATIC` joint;
* X-axis sliding motion;
* reasonable motion limit;
* separate Y-depth tracks;
* no obvious Viewer interpenetration.

## 17. One-Sentence Summary

This object is a successful articulated sliding window because a movable glass pane uses a horizontal `PRISMATIC` joint to slide across a fixed pane on a separate depth track while remaining inside the window frame.
