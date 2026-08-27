# Case 05 - Simple Cabinet V1

## 1. Object Name

Simple Cabinet V1

The object name in the code is:

```python
model = ArticulatedObject(name="hinged_door_sliding_drawer_cabinet")
```

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and the `gpt-5.5` model.

The goal was to create a combined articulated cabinet with:

* one fixed cabinet frame;
* one upper sliding drawer;
* one lower hinged cabinet door.

This case is more complex than the previous single-joint examples because it combines both a `PRISMATIC` joint and a `REVOLUTE` joint in one object.

## 3. Object Structure

The object contains three main parts:

1. `frame`
2. `door`
3. `drawer`

The `frame` is the fixed parent structure.

The `door` is a movable child part connected to the frame through a hinge joint.

The `drawer` is another movable child part connected to the frame through a sliding joint.

## 4. Cabinet Frame

The cabinet frame is built from several box-shaped visual elements:

* `side_panel_0`
* `side_panel_1`
* `top_panel`
* `bottom_panel`
* `back_panel`
* `middle_divider`
* `drawer_rail_0`
* `drawer_rail_1`

The frame defines the overall cabinet body.

The `middle_divider` separates the upper drawer section from the lower cabinet door section.

The drawer rails visually support the sliding drawer.

## 5. Lower Door Part

The lower cabinet door is defined as a separate part:

```python
door = model.part("door")
```

The door contains:

* `door_panel`
* `hinge_leaf`
* `door_pull`

The door panel is the main visual surface.

The hinge leaf visually represents the hinge-side connection.

The door pull represents the handle.

The key geometry design is:

```python
door.visual(
    Box((door_w, door_t, lower_opening_h)),
    origin=Origin(xyz=(door_w / 2.0, 0.0, lower_center_z)),
    material=panel_mat,
    name="door_panel",
)
```

The door panel is offset by `door_w / 2.0` in the local X direction. This means the left edge of the door is intended to be near the joint origin.

Therefore, the door is not simply rotating around its center. The code is trying to make the door rotate around its left edge.

## 6. Door Joint / REVOLUTE Articulation

The lower door articulation is:

```python
model.articulation(
    "door_hinge",
    ArticulationType.REVOLUTE,
    parent=frame,
    child=door,
    origin=Origin(xyz=(hinge_x, door_y, 0.0)),
    axis=(0.0, 0.0, -1.0),
    motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=0.0, upper=math.pi / 2.0),
)
```

My understanding:

* The joint name is `door_hinge`.
* The joint type is `REVOLUTE`.
* The parent part is `frame`.
* The child part is `door`.
* The axis is `(0.0, 0.0, -1.0)`.
* The motion limit is from `0` to `math.pi / 2.0`.

This means the lower door rotates around a vertical axis and opens about 90 degrees.

The axis direction is reasonable for a cabinet door.

## 7. Upper Drawer Part

The drawer is defined as another movable part:

```python
drawer = model.part("drawer")
```

The drawer contains:

* `front_panel`
* `tray_bottom`
* `tray_side_0`
* `tray_side_1`
* `tray_back`
* `tray_front_wall`
* `drawer_runner_0`
* `drawer_runner_1`
* `drawer_pull`

The drawer is not just a solid block. It has an open tray-like structure.

This is better than a simple solid drawer box because it has a more realistic storage area.

## 8. Drawer Joint / PRISMATIC Articulation

The drawer articulation is:

```python
model.articulation(
    "drawer_slide",
    ArticulationType.PRISMATIC,
    parent=frame,
    child=drawer,
    origin=Origin(),
    axis=(0.0, -1.0, 0.0),
    motion_limits=MotionLimits(effort=12.0, velocity=0.5, lower=0.0, upper=0.22),
)
```

My understanding:

* The joint name is `drawer_slide`.
* The joint type is `PRISMATIC`.
* The parent part is `frame`.
* The child part is `drawer`.
* The axis is `(0.0, -1.0, 0.0)`.
* The motion limit is from `0.0` to `0.22`.

This means the drawer slides outward along the negative Y direction.

This is appropriate for a drawer.

## 9. Viewer Observation

The model can be loaded in the Articraft Viewer.

The upper drawer can slide outward.

The lower cabinet door can rotate open.

Therefore, the overall structure is functional.

However, there is one visible issue:

The lower cabinet door hinge does not look fully realistic. The hinge-side edge of the door does not appear to be naturally attached to the cabinet body. The door can rotate, but the visual connection between the hinge and the cabinet frame looks slightly misaligned.

## 10. Main Issue

The main issue is:

```text
hinge alignment issue
```

More specifically:

```text
the door hinge is mathematically functional, but the hinge-side visual connection does not look physically realistic
```

This is different from a completely wrong joint type.

The generated code does use a `REVOLUTE` joint and a vertical hinge axis.

The problem is that the final visual motion still does not look perfectly realistic because the hinge line and the cabinet frame are not visually well integrated.

## 11. Tests / Validation

The test function checks several important things:

1. The cabinet frame is the fixed parent.
2. The door is the movable child.
3. The drawer is the movable child.
4. The door joint type is `REVOLUTE`.
5. The drawer joint type is `PRISMATIC`.
6. The door hinge axis is vertical.
7. The drawer slide axis is front-back.
8. The door motion limit is about 90 degrees.
9. The drawer motion limit is a partial extension.
10. The drawer has an open storage tray.
11. The door and drawer move outward.

The test for the door axis is:

```python
ctx.check(
    "door hinge axis is vertical",
    len(door_axis) == 3 and abs(abs(door_axis[2]) - 1.0) < 1e-6 and abs(door_axis[0]) < 1e-6 and abs(door_axis[1]) < 1e-6,
    details=f"axis={door_axis}",
)
```

The test for the drawer axis is:

```python
ctx.check(
    "drawer slide axis is front back",
    len(drawer_axis) == 3 and abs(abs(drawer_axis[1]) - 1.0) < 1e-6 and abs(drawer_axis[0]) < 1e-6 and abs(drawer_axis[2]) < 1e-6,
    details=f"axis={drawer_axis}",
)
```

These tests are useful, but they do not fully check whether the door hinge-side edge remains visually attached to the cabinet frame.

## 12. Why This Case Is Useful

This case is useful because it shows a more realistic problem in articulated object generation.

The object is not completely wrong.

It successfully combines:

* a fixed frame;
* a sliding drawer;
* a hinged door;
* one `PRISMATIC` joint;
* one `REVOLUTE` joint.

But it also shows that a generated model can pass many structural checks while still having visual realism issues.

This is important for future work because robot simulation needs not only mathematically valid joints, but also physically plausible geometry.

## 13. Lesson Learned

This case helped me understand that a hinge joint has three important components:

1. joint type;
2. joint axis;
3. joint origin and visual alignment.

The joint type and axis can be correct, but if the joint origin and visual hinge geometry are not well aligned with the frame, the object may still look unrealistic.

For future hinged objects, I need to check:

* whether the hinge line lies on the expected physical edge;
* whether the hinge-side edge stays close to the frame during motion;
* whether the door is flush with the opening when closed;
* whether the tests explicitly verify hinge alignment.

## 14. Status

This is an imperfect success case.

Successful parts:

* the model loads in the Viewer;
* the drawer slides outward;
* the lower door rotates open;
* the cabinet combines `PRISMATIC` and `REVOLUTE` joints;
* the drawer has an open storage tray.

Main issue:

* the lower door hinge connection does not look fully realistic in the Viewer.

## 15. One-Sentence Summary

This object is an imperfect articulated cabinet because it successfully combines a sliding drawer and a hinged door, but the lower door hinge is not visually well aligned with the cabinet frame, making the door motion look less realistic.
