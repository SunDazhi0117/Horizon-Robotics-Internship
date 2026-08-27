# Case 01 - Simple Single Door

## 1. Object Name

Simple Single Door

## 2. Generation Method

This object was generated using Articraft with the `codex-cli` provider.

The generation command was approximately:

```bash
uv run articraft generate \
  --provider codex-cli \
  --model gpt-5.5 \
  --thinking-level med \
  "Create a simple articulated single door..."
```

The generated object successfully passed compilation and can be viewed in the Articraft Viewer.

## 3. Object Structure

This object contains two main parts:

1. `frame`
2. `door`

The `frame` is the fixed part.

The `door` is the movable part.

This matches a real single door, where the frame stays still and the door panel rotates around the hinge.

## 4. Frame Part

The `frame` part is built from several simple box-shaped visual elements:

* `left_jamb`: the left side of the door frame
* `right_jamb`: the right side of the door frame
* `header`: the top rail of the frame
* `threshold`: the bottom rail of the frame
* `hinge_post`: the hinge-side post

These elements are mainly used to create the visible door frame in the Viewer.

## 5. Door Part

The `door` part is also built from simple box-shaped visual elements:

* `door_panel`: the main rectangular door panel
* `hinge_leaf`: the hinge plate attached to the door

The door panel is positioned relative to the door part so that the local origin of the door is close to the hinge side.

This is important because the door should rotate around its side edge, not around its center.

## 6. Joint / Articulation

The most important part of the code is the articulation:

```python
model.articulation(
    "frame_to_door",
    ArticulationType.REVOLUTE,
    parent=frame,
    child=door,
    origin=Origin(xyz=(-0.45, -0.04, 0.10)),
    axis=(0.0, 0.0, 1.0),
    motion_limits=MotionLimits(effort=20.0, velocity=2.0, lower=0.0, upper=pi / 2.0),
)
```

My understanding:

* The joint name is `frame_to_door`.
* The joint type is `REVOLUTE`.
* The parent part is `frame`.
* The child part is `door`.
* The joint axis is `(0, 0, 1)`.
* The motion limit is from `0` to `pi / 2`.

This means the door rotates around the vertical Z axis.

Since `pi / 2` equals 90 degrees, the door can open from 0 degrees to 90 degrees.

## 7. Motion Behavior

In the Viewer, the frame stays fixed.

The door panel rotates around the left vertical hinge.

This motion is reasonable for a simple single door.

The object is articulated because one part stays fixed while another part moves through a joint.

## 8. Tests / Validation

The `run_tests()` function checks whether the generated object is reasonable.

It mainly checks:

1. Whether the door hinge limit is from 0 to 90 degrees.
2. Whether the closed door is close to the left hinge side.
3. Whether the door clears the bottom threshold.
4. Whether the door clears the top header.
5. Whether the door panel fits within the frame width.
6. Whether the door opens outward after rotating 90 degrees.

These tests help verify that the door is not only visually correct, but also structurally reasonable.

## 9. Issue During Generation

The first compile attempt failed because one test condition was too broad.

The original test checked whether the `door_panel` was inside the `header` in both the x and z directions.

However, the `header` is only the top rail of the frame, so it should not contain the full height of the door panel in the z direction.

Codex changed the test to check only the x direction.

After this change, the model compiled successfully.

This shows that during articulated object generation, problems may come not only from the model itself, but also from incorrect or overly strict test conditions.

## 10. Current Limitation

The code mainly uses `visual` geometry.

I did not clearly see separate `collision` geometry definitions in this version.

The next step is to check whether the Viewer shows any collision warnings and whether the object is suitable for physics simulation.

## 11. One-Sentence Summary

This object is a simple articulated door because it has a fixed `frame` part and a movable `door` part connected by a `REVOLUTE` joint, allowing the door to rotate around a vertical hinge axis from 0 to 90 degrees.

