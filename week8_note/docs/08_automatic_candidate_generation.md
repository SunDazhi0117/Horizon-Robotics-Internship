# Automatic Work-Pose and Detour Candidate Generation

## Motivation

Candidate fallback can reject a colliding route automatically, but the previous YAML still listed explicit offsets for `preferred` and `backup_right`. The upgraded version lets the configuration describe a search region while Python generates candidate work poses and detour points.

## Search Rules Stored in the Configuration

    candidate_search:
      stand_distance: 0.60
      center_angle_degrees: -118.27257832
      angle_offsets_degrees: [0.0, 28.27257832, -25.0, 55.0, -55.0]
      detour_distance: 1.25

These parameters mean:

- every robot work pose is `0.60 m` from the target handle;
- search starts from a center direction in the target-local frame;
- angular offsets are tried to the left and right in the listed order;
- each candidate first visits an outer detour point `1.25 m` from the target in the same direction.

The configuration no longer lists each 2D coordinate separately.

## Candidate Generation

For each angle, the program computes:

    x_offset = distance * cos(angle)
    y_offset = distance * sin(angle)

The same calculation uses `detour_distance` for the outer detour point. All offsets are expressed in the target-handle frame, so they follow target translation and rotation.

`move_near_target` transforms each generated candidate into world coordinates, creates a dense base trajectory, and checks every state for environment overlap. A collision is recorded, and selection continues with the next candidate.

The summary stores the local offset, world-space waypoints, route length, status, and failure reason for every attempt. This makes the automatic choice auditable instead of returning only a final candidate number.

## Blocked-Preferred Result

The red cylinder remains in the original preferred work region:

- `auto_01`: conflicts with the obstacle and is rejected;
- `auto_02`: has a safe detour route and is selected;
- selected phase: `navigate_to_microwave_auto_02`.

After selection, the task reuses `approach_target`, `grasp_target`, and `follow_hinge_joint` to complete the full operation.

## Complete Acceptance Result

- Result: PASS
- States: 504
- Actions: 11
- Maximum door angle: `1.0 rad`
- Final door angle: `0.0 rad`
- Visual-overlap failures: 0
- Forbidden-contact failures: 0
- Grasp-loss failures: 0
- Maximum adjacent arm-joint step: `0.0760742 rad`
- Front and top-view frames: 169 each
- Week 8 tests: 10/10 passed

## Current Boundary

The system generates discrete target-relative candidates, not a continuous global path search. Search distance, center angle, angular offsets, and candidate order are still configured. Navigation collision checks select a route, while complete task execution determines whether the selected pose is also suitable for manipulation. A future version can add manipulation-reachability scoring or use A* or RRT to generate more complex obstacle-avoidance routes.
