# Level 5 Sequential Two-Door Opening Evaluation

## Task Definition

The robot first grasps the right-door handle and opens that door to 90 degrees. It then releases, retreats, travels around the outside of the cabinet to the left-door work pose, grasps the left handle, and opens the left door to 90 degrees.

The base remains locked while opening the right door. During left-door opening, the base and arm retreat together along a trajectory checked against the full environment to avoid the adjacent microwave counter.

## Local Acceptance Criteria

- Both doors finish at no less than 85 degrees.
- Base drift while opening the right door is no greater than `1e-9`.
- Left-door opening uses an explicitly recorded controlled base trajectory.
- Each door angle changes only during its own opening phase.
- Both opening trajectories are monotonically increasing.
- Both fingers retain contact while manipulating each handle.
- Maximum gripper-to-active-handle distance is no greater than `0.06 m`.
- Maximum adjacent arm-joint step is no greater than `0.20 rad`.
- Visual overlaps with the target cabinet, adjacent microwave counter, and other static furniture total 0.
- Illegal non-finger contact with the active handle totals 0.

## Result

Local deterministic evaluation: `PASS`, score `100/100`.

- Final right-door angle: `90 deg`
- Final left-door angle: `90 deg`
- Right-door opening samples: `65`
- Left-door opening samples: `65`
- Total validated states: `429`
- Minimum valid finger contacts on right handle: `2`
- Minimum valid finger contacts on left handle: `2`
- Maximum arm-joint step: `0.1113531 rad`
- Full-environment visual-overlap failures: `0`
- Illegal handle-contact failures: `0`

This result evaluates a scripted trajectory in a custom MuJoCo scene. It is neither an official RoboDojo score nor a closed-loop policy evaluation.
