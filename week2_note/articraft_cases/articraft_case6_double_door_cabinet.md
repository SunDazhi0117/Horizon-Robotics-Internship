# Case 06 - Double-Door Storage Cabinet

## 1. Object Name

Double-Door Storage Cabinet

The object name in the generated code is:

```python
model = ArticulatedObject(name="double_door_storage_cabinet")
```

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and the `gpt-5.5` model.

The goal was to create a simple storage cabinet with two independently movable doors.

This case focuses on:

* multiple movable parts;
* two separate `REVOLUTE` joints;
* mirrored hinge placement;
* opposite opening directions;
* closed-pose alignment and center clearance.

## 3. Object Structure

The object contains three main parts:

1. `cabinet_frame`
2. `left_door`
3. `right_door`

The `cabinet_frame` is the fixed root part.

The `left_door` and `right_door` are separate movable child parts.

Both doors are connected directly to the fixed cabinet frame.

## 4. Cabinet Frame

The cabinet frame is constructed from simple box-shaped visual elements:

* `left_side_panel`
* `right_side_panel`
* `top_panel`
* `bottom_panel`
* `back_panel`
* `internal_shelf`

The two side panels, top panel, bottom panel and back panel form the main cabinet body.

The internal shelf divides the storage space and makes the cabinet structure more realistic.

## 5. Door Dimensions and Center Gap

The cabinet dimensions are defined by constants:

```python
CABINET_W = 1.00
CABINET_D = 0.42
CABINET_H = 1.20
PANEL_T = 0.04
DOOR_T = 0.035
CENTER_GAP = 0.006
```

The width of each door is calculated as:

```python
door_w = inner_w / 2.0 - CENTER_GAP / 2.0
```

This leaves a small gap between the two closed doors.

The center gap is approximately 6 mm, which prevents the doors from overlapping when closed.

## 6. Left Door Geometry

The left door is defined as:

```python
left_door = model.part("left_door")
```

Its main door slab uses:

```python
origin=Origin(
    xyz=(door_w / 2.0, -DOOR_T / 2.0, CABINET_H / 2.0)
)
```

Because the local X position is `door_w / 2.0`, the door panel extends from the local origin toward the positive X direction.

This places the local origin on the left edge of the door.

Therefore, the left door is designed to rotate around its own left edge rather than around its center.

## 7. Right Door Geometry

The right door is defined as:

```python
right_door = model.part("right_door")
```

Its main door slab uses:

```python
origin=Origin(
    xyz=(-door_w / 2.0, -DOOR_T / 2.0, CABINET_H / 2.0)
)
```

Because the local X position is `-door_w / 2.0`, the door panel extends from the local origin toward the negative X direction.

This places the local origin on the right edge of the door.

Therefore, the right door is designed to rotate around its own right edge.

The left and right door geometry is mirrored.

## 8. Left Door Joint

The left door articulation is:

```python
model.articulation(
    "left_hinge",
    ArticulationType.REVOLUTE,
    parent=frame,
    child=left_door,
    origin=Origin(xyz=(left_hinge_x, front_y, 0.0)),
    axis=(0.0, 0.0, -1.0),
    motion_limits=MotionLimits(
        effort=12.0,
        velocity=2.0,
        lower=0.0,
        upper=OPEN_ANGLE,
    ),
)
```

My understanding:

* joint name: `left_hinge`
* joint type: `REVOLUTE`
* parent: `cabinet_frame`
* child: `left_door`
* axis: `(0.0, 0.0, -1.0)`
* motion range: 0 to 90 degrees

The hinge origin is placed on the left vertical front edge of the cabinet opening.

## 9. Right Door Joint

The right door articulation is:

```python
model.articulation(
    "right_hinge",
    ArticulationType.REVOLUTE,
    parent=frame,
    child=right_door,
    origin=Origin(xyz=(right_hinge_x, front_y, 0.0)),
    axis=(0.0, 0.0, 1.0),
    motion_limits=MotionLimits(
        effort=12.0,
        velocity=2.0,
        lower=0.0,
        upper=OPEN_ANGLE,
    ),
)
```

My understanding:

* joint name: `right_hinge`
* joint type: `REVOLUTE`
* parent: `cabinet_frame`
* child: `right_door`
* axis: `(0.0, 0.0, 1.0)`
* motion range: 0 to 90 degrees

The hinge origin is placed on the right vertical front edge of the cabinet opening.

## 10. Why the Doors Open in Opposite Directions

The two hinge axes are:

```python
left_axis = (0.0, 0.0, -1.0)
right_axis = (0.0, 0.0, 1.0)
```

Both doors use a positive joint range from 0 to 90 degrees.

However, the Z-axis directions are opposite.

As a result:

* the left door opens outward toward the left side;
* the right door opens outward toward the right side.

This creates the correct double-door opening motion.

## 11. Tests and Validation

The generated `run_tests()` function checks:

1. The cabinet frame is the fixed parent.
2. The two doors are movable child parts.
3. Both joints are `REVOLUTE`.
4. Both hinge axes are vertical.
5. The two doors open in opposite directions.
6. The left hinge is placed on the left front edge.
7. The right hinge is placed on the right front edge.
8. Both motion limits are approximately 90 degrees.
9. The closed doors meet with a small center clearance.
10. The closed doors sit flush with the cabinet front.
11. The closed doors cover the cabinet opening height.
12. The open doors remain clear of the cabinet frame.
13. The open doors remain separated from each other.
14. Both doors move outward in the open pose.
15. The cabinet contains an open storage cavity.

The hinge-origin tests compare the actual joint origins with the expected physical cabinet edges.

This is particularly useful because it checks the issue observed in the previous Simple Cabinet V1 case.

## 12. Viewer Observation

The model loaded successfully in the Articraft Viewer.

The visual structure looked reasonable.

The left and right doors could be controlled independently.

The left door rotated around the left side of the cabinet opening.

The right door rotated around the right side of the cabinet opening.

The two doors opened in opposite directions.

No obvious severe interpenetration or hinge misalignment was observed.

## 13. Comparison with Simple Cabinet V1

In Simple Cabinet V1, the lower door could rotate, but the hinge-side connection did not look fully integrated with the cabinet frame.

In this double-door cabinet, the code explicitly calculates and tests the left and right hinge origins:

```python
left_hinge_x = -half_w + PANEL_T
right_hinge_x = half_w - PANEL_T
```

The door panels are also offset in opposite local directions.

This results in more natural hinge placement and more realistic door movement.

## 14. Current Limitations

This version mainly defines visual geometry.

Separate explicit collision geometry is not clearly defined.

The hinge is mathematically represented by the joint, but there are no detailed hinge barrels or hinge plates.

The storage-cavity test uses bounding boxes and door positions to infer that the cabinet interior is open. It does not yet test whether another object can physically fit inside the cabinet.

## 15. Status

This is a successful case.

Successful features:

* fixed cabinet frame;
* two movable doors;
* two independent `REVOLUTE` joints;
* correct mirrored door geometry;
* correct hinge origins;
* opposite opening directions;
* approximately 90-degree motion limits;
* small center clearance in the closed pose;
* no obvious Viewer interpenetration.

## 16. One-Sentence Summary

This object is a successful double-door articulated cabinet because two mirrored door parts are connected to the fixed cabinet frame by separate `REVOLUTE` joints with correctly positioned hinge origins and opposite vertical axis directions.
