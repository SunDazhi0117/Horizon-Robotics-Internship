## Failure Case - Simple Cabinet V1: Door Hinge Origin Misalignment

### Object

Simple articulated cabinet with one upper sliding drawer and one lower hinged cabinet door.

### Status

Imperfect success.

The model can be loaded in the Viewer, and both the upper drawer and lower door appear to be articulated. The drawer can slide outward, and the lower cabinet door can rotate open.

However, the lower door does not rotate in a fully realistic way.

### Observed Problem

The lower cabinet door appears to rotate around an axis that is not perfectly aligned with the cabinet body.

The hinge-side edge of the door is not closely attached to the left vertical front edge of the lower cabinet opening. As a result, the door looks like it is rotating around a slightly detached or floating hinge axis.

### Failure Type

Hinge origin misalignment.

This is different from a completely wrong joint type or wrong joint axis.

The joint is likely still a `REVOLUTE` joint, and the axis is likely vertical. The main issue is that the joint origin is not placed exactly on the expected hinge line.

### Why This Matters

For a realistic cabinet door, the hinge origin should lie on the left vertical front edge of the cabinet opening.

The door should rotate around its own left edge. When the door opens, the hinge-side edge should remain close to the cabinet frame.

If the hinge origin is offset from the frame, the door may still rotate, but the motion will look physically unrealistic.

### Possible Cause

The likely cause is that the generated code placed the `REVOLUTE` joint origin in an approximate position, but not exactly on the visual hinge edge of the cabinet frame.

Another possible cause is that the door panel geometry is not correctly offset relative to the joint origin. If the door panel is centered around the joint instead of extending from the hinge edge, the door may appear to rotate around an unnatural axis.

### Lesson Learned

A generated articulated object can have the correct joint type and joint axis, but still look unrealistic if the joint origin is not aligned with the intended physical hinge location.

For hinged doors, checking the joint origin is as important as checking the joint axis.

### Future Improvement

In the next prompt or manual correction, explicitly require:

* the door hinge origin must lie exactly on the left vertical front edge of the lower cabinet opening;
* the door must rotate around its own left edge;
* the door must not rotate around its center;
* the hinge-side edge of the door should remain close to the cabinet frame during opening;
* the closed door should sit flush with the cabinet front.
