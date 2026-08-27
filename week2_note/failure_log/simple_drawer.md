## Failure Case - Simple Drawer V1: Visual Interpenetration

### Object

Simple articulated drawer V1

### Generation Method

The object was generated using Articraft with the `codex-cli` provider and `gpt-5.5` model.

### Problem Observed

The model successfully passed compilation and could be opened in the Articraft Viewer. However, during manual Viewer inspection, the drawer front appeared to visually intersect with the cabinet frame.

The issue was most obvious around the lower front rail and side frame area. When the drawer was pulled out, part of the lower/front region showed clear visual inconsistency. The drawer front seemed to overlap or pass into the grey cabinet frame.

### Code-Level Observation

From the generated code, the drawer front is defined as:

```python
drawer.visual(
    Box((0.33, 0.035, 0.13)),
    origin=Origin(xyz=(0.0, -0.155, 0.105)),
    material=drawer_mat,
    name="drawer_front",
)
```

The cabinet lower front rail is defined as:

```python
cabinet.visual(
    Box((0.40, 0.03, 0.035)),
    origin=Origin(xyz=(0.0, -0.195, 0.0475)),
    material=cabinet_mat,
    name="front_lower_rail",
)
```

The `drawer_front` and `front_lower_rail` have overlapping height ranges. This likely causes the drawer front to visually conflict with the cabinet frame.

### My Understanding

The core articulation structure is correct:

* `cabinet` is the fixed parent part.
* `drawer` is the movable child part.
* The joint type is `PRISMATIC`.
* The joint axis is `(0.0, -1.0, 0.0)`.
* The drawer slides outward along the front-back direction.

However, the visual geometry is not clean. The drawer front is too close to or partially overlapping with the cabinet frame.

### Lesson Learned

Passing compilation does not always mean the object is visually clean or physically realistic.

Manual Viewer inspection is still necessary, especially for articulated objects with moving parts.

### Next Step

Generate a cleaner drawer V2 with a stricter prompt:

* The drawer front should sit outside the cabinet opening.
* The drawer front must not intersect the cabinet side panels, top rail, or bottom rail.
* There should be visible clearance around the drawer front.
* The validation tests should check no visual overlap in both closed and open poses.
