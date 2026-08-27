# Case 04 - Box with Hinged Lid

## 1. Object Name

Box with Hinged Lid

The object name in the code is:

```python
model = ArticulatedObject(name="hinged_storage_box")
```

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider and the `gpt-5.5` model.

The goal was to create a simple open-top storage box with a movable hinged lid.

## 3. Object Structure

This object contains two main parts:

1. `box_base`
2. `lid`

The `box_base` is the fixed parent part.

The `lid` is the movable child part.

This structure matches a real hinged box, where the box body stays fixed and the lid rotates around a hinge.

## 4. Box Base Part

The `box_base` is built from several simple box-shaped visual elements:

* `bottom_panel`
* `front_wall`
* `back_wall`
* `side_wall_0`
* `side_wall_1`
* `hinge_strip`

The box base has an open-top storage cavity.

It is not a solid block because it has walls and a bottom panel, but no `top_panel`.

## 5. Lid Part

The `lid` part is built from:

* `lid_panel`
* `hinge_leaf`

The lid is a flat rectangular panel attached near the back edge of the box.

The `hinge_leaf` visually represents the hinge connection between the lid and the box base.

## 6. Joint / Articulation

The key articulation is:

```python
model.articulation(
    "lid_hinge",
    ArticulationType.REVOLUTE,
    parent=base,
    child=lid,
    origin=Origin(xyz=(length / 2.0 + 0.003, 0.0, wall_top_z + 0.004)),
    axis=(0.0, 1.0, 0.0),
    motion_limits=MotionLimits(
        effort=4.0,
        velocity=2.0,
        lower=0.0,
        upper=math.radians(100.0),
    ),
)
```

My understanding:

* The joint name is `lid_hinge`.
* The joint type is `REVOLUTE`.
* The parent part is `box_base`.
* The child part is `lid`.
* The hinge axis is `(0.0, 1.0, 0.0)`.
* The motion limit is from `0` degrees to about `100` degrees.

This means the lid rotates around a horizontal hinge axis along the back edge of the box.

## 7. Motion Behavior

In the Viewer, the box base stays fixed.

The lid rotates upward around the back hinge.

This motion is reasonable for a hinged storage box.

The object is articulated because one part stays fixed while another part rotates through a joint.

## 8. Storage Area

The box has a visible storage area because it is made from:

* a bottom panel
* a front wall
* a back wall
* two side walls

There is no `top_panel`, so the inside of the box remains open.

This makes the object a storage box instead of a solid block.

## 9. Tests / Validation

The `run_tests()` function checks several important conditions:

1. The box base is the fixed parent.
2. The lid is the movable child.
3. The hinge joint is `REVOLUTE`.
4. The hinge axis is horizontal.
5. The motion limit is reasonable.
6. The box has an open storage cavity.
7. The closed lid covers the storage footprint.
8. The open lid stays clear of the box walls.
9. The lid opens upward.

The most important motion test checks whether the lid is higher after opening:

```python
ctx.check(
    "lid opens upward",
    closed_lid_aabb is not None
    and open_lid_aabb is not None
    and ((open_lid_aabb[0][2] + open_lid_aabb[1][2]) / 2.0)
    > ((closed_lid_aabb[0][2] + closed_lid_aabb[1][2]) / 2.0) + 0.05,
)
```

This confirms that the lid actually moves upward after rotation.

## 10. Viewer Observation

The model can be loaded and moved in the Articraft Viewer.

The lid opens upward as expected.

The colorful appearance seen in the Viewer was caused by enabling the collision box display mode. The normal visual appearance is acceptable.

No obvious severe interpenetration was observed during manual inspection.

## 11. Current Limitation

This version mainly uses visual geometry.

I did not clearly see separate explicit collision geometry definitions in the code.

Therefore, the articulated structure and Viewer motion are correct, but the physical simulation quality still needs further checking.

## 12. Status

This is a successful case.

It satisfies the main requirements:

* fixed open-top box base
* movable lid
* `REVOLUTE` hinge joint
* horizontal hinge axis
* upward lid motion
* visible storage area
* successful Viewer loading and motion

## 13. One-Sentence Summary

This object is a successful articulated box with lid because it has a fixed open-top `box_base` and a movable `lid` connected by a `REVOLUTE` hinge joint, allowing the lid to rotate upward around a horizontal hinge axis.
