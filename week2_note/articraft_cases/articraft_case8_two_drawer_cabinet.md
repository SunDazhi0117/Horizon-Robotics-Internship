# Case 08 - Two-Drawer Cabinet

## 1. Object Name

Two-Drawer Cabinet

The generated object name is:

```python
model = ArticulatedObject(name="two_drawer_sliding_cabinet")
```

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and the `gpt-5.5` model.

The goal was to create a cabinet with two independently movable sliding drawers.

This case focuses on:

* two independent `PRISMATIC` joints;
* multiple movable child parts;
* open-top drawer trays;
* drawer support rails;
* joint independence.

## 3. Object Structure

The model contains three main parts:

1. `cabinet_frame`
2. `upper_drawer`
3. `lower_drawer`

The structure is:

```text
cabinet_frame
├── upper_slide → upper_drawer
└── lower_slide → lower_drawer
```

The cabinet frame is the fixed parent structure.

The upper and lower drawers are separate movable child parts.

## 4. Cabinet Frame

The cabinet frame contains:

* `left_side_panel`
* `right_side_panel`
* `top_panel`
* `bottom_panel`
* `back_panel`
* `middle_divider`
* `upper_rail_0`
* `upper_rail_1`
* `lower_rail_0`
* `lower_rail_1`

The middle divider separates the upper and lower drawer compartments.

Each drawer has two support rails.

## 5. Reusable Drawer Function

The generated code defines:

```python
def _add_drawer(part, z_center: float) -> None:
```

This helper function creates the complete geometry for one drawer.

It is called twice:

```python
_add_drawer(upper, UPPER_Z)
_add_drawer(lower, LOWER_Z)
```

This avoids duplicating the same drawer-construction code.

The two drawer structures are identical, but they are placed at different heights.

## 6. Drawer Structure

Each drawer contains:

* `tray_bottom`
* `side_wall_0`
* `side_wall_1`
* `back_wall`
* `front_wall`
* `front_panel`
* `handle`

The drawer is built from separate box panels.

There is no `top_wall`, so each drawer contains an open storage cavity.

This is more realistic than representing the drawer as a single solid box.

## 7. Upper and Lower Positions

The drawer center heights are:

```python
LOWER_Z = 0.181
UPPER_Z = 0.519
```

The height difference is approximately:

```text
0.338 metres
```

The drawer height is:

```python
DRAWER_H = 0.20
```

Therefore, the upper and lower drawers are vertically separated and do not overlap.

## 8. Upper Drawer Joint

The upper drawer articulation is:

```python
model.articulation(
    "upper_slide",
    ArticulationType.PRISMATIC,
    parent=frame,
    child=upper,
    origin=Origin(xyz=(0.0, DRAWER_CLOSED_Y, 0.0)),
    axis=(0.0, -1.0, 0.0),
    motion_limits=limits,
)
```

My understanding:

* joint name: `upper_slide`
* joint type: `PRISMATIC`
* parent: `cabinet_frame`
* child: `upper_drawer`
* axis: negative Y direction
* lower limit: `0.0`
* upper limit: `0.22` metres

The upper drawer therefore slides outward from the cabinet front.

## 9. Lower Drawer Joint

The lower drawer articulation is:

```python
model.articulation(
    "lower_slide",
    ArticulationType.PRISMATIC,
    parent=frame,
    child=lower,
    origin=Origin(xyz=(0.0, DRAWER_CLOSED_Y, 0.0)),
    axis=(0.0, -1.0, 0.0),
    motion_limits=limits,
)
```

My understanding:

* joint name: `lower_slide`
* joint type: `PRISMATIC`
* parent: `cabinet_frame`
* child: `lower_drawer`
* axis: negative Y direction
* lower limit: `0.0`
* upper limit: `0.22` metres

The lower drawer can move independently from the upper drawer.

## 10. Motion Limits

Both drawers use:

```python
MotionLimits(
    effort=80.0,
    velocity=0.5,
    lower=0.0,
    upper=0.22,
)
```

The maximum extension is 22 cm.

The drawer depth is 34 cm.

Therefore, when fully opened, part of the drawer remains inside the cabinet.

This is a reasonable partial-extension design.

## 11. Closed Front Alignment

The drawer joint origin and front-panel local position are calculated together.

This places the outside surface of each front panel close to the cabinet front plane when the joint position is zero.

As a result, the closed drawers appear approximately flush with the cabinet front.

## 12. Support Rails

The cabinet contains two rails for each drawer.

The rail height is calculated from the drawer center and height:

```python
rail_z = z_center - DRAWER_H / 2.0 - rail_h / 2.0
```

The drawer tray bottom is positioned directly above the rails.

Validation tests require a very small vertical gap between the tray bottom and the support rail.

This helps prevent the drawers from appearing to float.

## 13. Joint Independence

The generated tests open each drawer separately.

When the upper drawer is opened, the lower drawer position is checked to confirm that it remains unchanged.

When the lower drawer is opened, the upper drawer position is checked in the same way.

This confirms that the object has two independent degrees of freedom.

## 14. Tests and Validation

The generated tests check:

1. The cabinet frame is the parent of both drawer joints.
2. The upper and lower drawers are movable children.
3. Both joints are `PRISMATIC`.
4. Both axes point toward the cabinet front.
5. Both motion limits are reasonable.
6. Both drawers are open-top trays.
7. The drawers are located at different heights.
8. The drawer fronts remain within the cabinet width.
9. The tray front walls remain behind the external face panels.
10. The tray backs clear the cabinet back panel.
11. The drawer fronts clear the cabinet top and bottom areas.
12. The drawers do not overlap vertically.
13. Both drawers sit above support rails.
14. Both drawers remain laterally supported when open.
15. The upper drawer slides outward.
16. The lower drawer slides outward.
17. The two joints operate independently.

## 15. Viewer Observation

The object loaded successfully in the Articraft Viewer.

The cabinet frame remained fixed.

The upper and lower drawers could be controlled separately.

Both drawers moved outward along the front-back direction.

Opening one drawer did not move the other drawer.

Both drawers contained visible open storage trays.

No obvious severe interpenetration was observed.

## 16. Why This Case Is Useful

Previous drawer cases contained only one sliding drawer.

This case demonstrates:

* two independent movable child parts;
* two independent `PRISMATIC` joints;
* multiple degrees of freedom;
* reusable geometry-generation functions;
* independent task states for upper and lower drawers.

It also forms a useful comparison with the double-door cabinet:

```text
Double-Door Cabinet:
two independent REVOLUTE joints

Two-Drawer Cabinet:
two independent PRISMATIC joints
```

## 17. Current Limitations

The object mainly defines visual geometry.

Explicit collision geometry is not clearly defined.

The validation tests do not test both drawers being fully open at the same time.

The open-pose support test mainly checks lateral overlap and does not fully verify remaining support along the drawer depth.

The physical effects of gravity, friction and rail contact have not yet been tested in SAPIEN or MuJoCo.

The upper and lower heights are defined inside the drawer visual coordinates instead of through separate joint Z origins. This works, but a more modular implementation could center each drawer locally and use joint origins to place the two drawers.

## 18. Status

This is a successful case.

Successful features include:

* fixed cabinet frame;
* two movable drawers;
* two independent `PRISMATIC` joints;
* open storage trays;
* reasonable motion limits;
* separate vertical positions;
* support rails;
* independent drawer movement;
* no obvious Viewer interpenetration.

## 19. One-Sentence Summary

This object is a successful articulated two-drawer cabinet because two open-top drawer parts are connected independently to a fixed cabinet frame through separate `PRISMATIC` joints, allowing each drawer to slide outward without moving the other.
