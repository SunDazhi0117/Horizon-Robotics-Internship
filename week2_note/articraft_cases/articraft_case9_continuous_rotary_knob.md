# Case 09 - Continuous Rotary Knob

## 1. Object Name

Continuous Rotary Knob

The generated object name is:

```python
model = ArticulatedObject(
    name="continuous_rotary_control_knob"
)
```

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and the `gpt-5.5` model.

The goal was to create a simple control knob that could rotate continuously around its own central vertical axis.

This case focuses on:

* a `CONTINUOUS` joint;
* unlimited rotational motion;
* a centered vertical rotation axis;
* visible orientation markers;
* the difference between continuous motion and Viewer angle display.

## 3. Object Structure

The model contains two parts:

1. `base`
2. `knob`

The kinematic structure is:

```text
base
└── CONTINUOUS joint → knob
```

The `base` is the fixed root part.

The `knob` is the movable child part.

The two parts are connected through the articulation:

```python
base_to_knob
```

## 4. Fixed Base

The base is created as a low rectangular block:

```python
base.visual(
    Box((0.24, 0.18, 0.035)),
    origin=Origin(xyz=(0.0, 0.0, 0.0175)),
    name="base_block",
)
```

Its dimensions are:

```text
Width along X:  0.24 m
Depth along Y:  0.18 m
Height along Z: 0.035 m
```

The base center is positioned at:

```text
Z = 0.0175 m
```

Because the base height is `0.035 m`, its bottom is located at `Z = 0`, so it rests directly on the ground plane.

## 5. Knob Structure

The movable `knob` part contains five visual elements:

* `knob_body`
* `center_spindle`
* `pointer_bar`
* `grip_bar_0`
* `grip_bar_1`

### Knob body

The main knob body is:

```python
Box((0.085, 0.085, 0.045))
```

It is represented using box geometry.

Although many real control knobs are cylindrical, the box-shaped geometry is sufficient for learning and validating the rotational joint.

### Center spindle

The center spindle is:

```python
Box((0.024, 0.024, 0.006))
```

It is placed beneath the main knob body.

Its purposes are:

* to visually connect the knob to the base;
* to represent the central mounting shaft;
* to prevent the knob from appearing to float;
* to provide a clear contact element for validation.

### Pointer bar

The pointer bar is:

```python
Box((0.012, 0.052, 0.008))
```

It is placed slightly away from the center of the knob:

```python
origin=Origin(xyz=(0.0, 0.018, 0.049))
```

The pointer makes the orientation of the knob visible.

Without this asymmetric marker, it would be difficult to observe rotation on a nearly symmetric knob.

### Grip bars

The knob also contains two grip bars:

```text
grip_bar_0
grip_bar_1
```

They are positioned on opposite sides of the knob.

These bars provide additional visual information about the knob orientation during rotation.

## 6. Joint Definition

The articulation is:

```python
model.articulation(
    "base_to_knob",
    ArticulationType.CONTINUOUS,
    parent=base,
    child=knob,
    origin=Origin(xyz=(0.0, 0.0, 0.041)),
    axis=(0.0, 0.0, 1.0),
    motion_limits=MotionLimits(
        effort=1.0,
        velocity=6.0,
    ),
)
```

My understanding:

* joint name: `base_to_knob`
* joint type: `CONTINUOUS`
* parent part: `base`
* child part: `knob`
* axis: positive Z direction
* effort: `1.0`
* velocity: `6.0`
* finite lower angle limit: none
* finite upper angle limit: none

## 7. Continuous Joint

The most important setting is:

```python
ArticulationType.CONTINUOUS
```

A continuous joint represents unlimited rotation.

Unlike a limited `REVOLUTE` joint, it does not have a finite lower or upper angular position.

The motion limits only contain:

```python
MotionLimits(
    effort=1.0,
    velocity=6.0,
)
```

There is no configuration such as:

```python
lower=-math.pi
upper=math.pi
```

Therefore, the model itself is not limited to the angular range from `-180°` to `180°`.

## 8. Rotation Axis

The joint axis is:

```python
axis=(0.0, 0.0, 1.0)
```

This axis is parallel to the Z axis.

Because Z is the vertical direction, the knob rotates horizontally around its vertical center line.

The rotation resembles the movement of:

* a control dial;
* a faucet handle;
* a stove knob;
* an industrial rotary selector.

## 9. Joint Origin

The joint origin is:

```python
Origin(xyz=(0.0, 0.0, 0.041))
```

The X and Y coordinates are both zero, so the joint axis passes through the center of the knob.

This prevents the knob from orbiting around an offset point.

The base top is located at:

```text
Z = 0.035 m
```

The spindle height is:

```text
0.006 m
```

Therefore:

```text
0.035 + 0.006 = 0.041 m
```

The joint origin is positioned at the top of the spindle and at the bottom center of the main knob body.

## 10. Vertical Geometry Relationship

The vertical arrangement is:

```text
Base top:          Z = 0.035 m
Spindle bottom:    Z = 0.035 m
Spindle top:       Z = 0.041 m
Knob body bottom:  Z = 0.041 m
```

This means:

* the spindle touches the base;
* the knob body rests above the spindle;
* the main knob body does not intersect the base;
* the complete knob assembly does not appear to float.

The gap between the main knob body and the base is:

```text
0.041 - 0.035 = 0.006 m
```

Therefore, the main body has a clearance of approximately 6 mm above the base.

## 11. Viewer Observation

The object loaded successfully in the Articraft Viewer.

The base remained fixed.

The knob rotated around its own vertical center axis.

The pointer and grip bars rotated together with the knob.

The knob did not visibly translate or orbit around an offset axis.

No obvious severe interpenetration was observed.

The Viewer displayed the joint angle within the range:

```text
-180° to 180°
```

However, this does not represent a finite joint limit.

The generated code explicitly uses a `CONTINUOUS` joint and does not define finite lower or upper angular bounds.

## 12. Viewer Angle Wrapping

Angles are periodic.

For example:

```text
270° is equivalent to -90°
360° is equivalent to 0°
450° is equivalent to 90°
```

The Viewer appears to normalize the displayed angle to the range:

```text
[-180°, 180°]
```

A possible display sequence is:

```text
Actual accumulated angle    Viewer display

0°                          0°
90°                         90°
180°                        180°
181°                        -179°
270°                        -90°
360°                        0°
540°                        180° or -180°
```

Therefore, the Viewer may display a wrapped single-turn angle even though the underlying articulation is continuous.

This is a display convention rather than a finite mechanical limit.

## 13. Tests and Validation

The generated tests check the following properties.

### Parent and child relationship

The tests confirm that:

```text
parent = base
child = knob
```

The knob is therefore the movable child of the fixed base.

### Continuous joint type

The test checks:

```python
joint.articulation_type == ArticulationType.CONTINUOUS
```

This confirms that the joint is not a limited `REVOLUTE` joint.

### Vertical axis

The test normalizes the joint axis and verifies that it is parallel to the Z axis.

Both of the following would represent a vertical axis:

```text
(0, 0, 1)
(0, 0, -1)
```

The sign only changes the positive direction of rotation.

### No finite angle bounds

The test checks:

```python
getattr(limits, "lower", None) is None
and getattr(limits, "upper", None) is None
```

This confirms that the continuous joint has no finite lower or upper angular position limit.

### Centered joint origin

The code calculates the XY center of the `knob_body` world-space AABB.

It then compares that center with the joint origin.

This verifies that the rotation axis passes through the center of the knob.

### Clearance above the base

The test requires the gap between the main knob body and the base to remain between:

```text
4 mm and 8 mm
```

The actual design gap is approximately:

```text
6 mm
```

### Spindle contact

The test checks that:

```text
center_spindle contacts base_block
```

This prevents the complete knob assembly from appearing unsupported.

### No translation during rotation

The test records the knob position before and after a 90-degree rotation.

It then confirms that the world position remains unchanged.

This demonstrates that the knob rotates in place rather than moving along a circular path.

### Pointer orientation change

The pointer bar has different X and Y dimensions.

After a 90-degree rotation, its world-space AABB dimensions should approximately exchange positions.

The test confirms that:

```text
initial X size ≈ rotated Y size
initial Y size ≈ rotated X size
```

This proves that the pointer changes orientation with the knob.

## 14. Why This Case Is Useful

Previous generated objects mainly used:

* `REVOLUTE` joints for limited rotational movement;
* `PRISMATIC` joints for translational movement.

This case introduces the third important movable joint type:

```text
CONTINUOUS
```

Comparison:

```text
REVOLUTE
- rotational movement
- finite angular limits
- example: door or hinged lid

PRISMATIC
- linear movement
- finite distance limits
- example: drawer or sliding window

CONTINUOUS
- rotational movement
- no finite angular position limits
- example: rotary knob or wheel
```

This case also demonstrates the difference between:

```text
actual joint capability
and
Viewer angle representation
```

## 15. Potential Robot Tasks

This object could later be used for robot tasks such as:

```text
Rotate the knob clockwise by 90 degrees.
```

```text
Rotate the knob counterclockwise by 45 degrees.
```

```text
Complete one full rotation of the knob.
```

```text
Move the pointer to a specified orientation.
```

For tasks requiring multiple full rotations, the simulation or task logic would need to track accumulated joint displacement rather than relying only on a normalized Viewer angle.

## 16. Current Limitations

The object mainly defines visual geometry.

Explicit collision geometry is not clearly defined.

The knob is box-shaped rather than cylindrical.

The validation tests rotate the joint by only 90 degrees.

They do not explicitly test:

* one full rotation;
* multiple full rotations;
* accumulated joint angle;
* rotational friction;
* damping;
* torque;
* physical contact with a robot gripper.

The test named `base is fixed root` primarily checks the parent-child relationship. A stricter version could also inspect `root_parts()` directly.

The dynamic behavior has not yet been validated in SAPIEN or MuJoCo.

## 17. Status

This is a successful case.

Successful features include:

* fixed base;
* separate movable knob;
* `CONTINUOUS` joint;
* no finite angle bounds;
* centered vertical rotation axis;
* no translation during rotation;
* visible direction marker;
* spindle contact with the base;
* reasonable clearance;
* no obvious Viewer interpenetration.

The Viewer angle range from `-180°` to `180°` is interpreted as an angle-wrapping display convention rather than a model limitation.

## 18. One-Sentence Summary

This object is a successful continuous rotary control because the knob is connected to a fixed base through an unlimited `CONTINUOUS` joint centered on the vertical Z axis, allowing in-place rotation while the Viewer represents the orientation using a wrapped angle from `-180°` to `180°`.
