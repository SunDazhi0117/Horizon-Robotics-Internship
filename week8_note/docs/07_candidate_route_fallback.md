# Candidate-Route Fallback Validation

## Goal

The previous stage updated one robot work pose from the target pose, but it failed if that pose was occupied by an obstacle. This stage upgrades `move_near_target` to validate several candidate routes in order.

## Configuration Representation

The configuration supplies two candidates:

    preferred:
      base_offset: [-0.32700001, -0.60800185]

    backup_right:
      path_offsets:
        - [0.08721821, -1.24627967]
      base_offset: [0.0, -0.60]

Every offset is expressed in the local frame of the target handle. Candidate goals and detour points therefore update together when the microwave is moved or rotated.

## Test Scene

An independent derived scene uses the translated and rotated microwave. A red cylinder with radius `0.11 m` is placed at the preferred work pose. Stable scenes and earlier results remain unchanged.

The program first generates the preferred route. Per-state validation detects visual overlap between the robot and the red cylinder, so that candidate is rejected. It then generates `backup_right`, which passes through a target-relative detour point before reaching the backup work pose.

## Why a Candidate Must Pass the Complete Task

The initial backup pose `[0.0, -0.72]` allowed safe navigation, approach, and grasping, but its arm-joint change exceeded `0.15 rad` while opening the door. Complete-task validation therefore rejected it. The final pose `[0.0, -0.60]` completed grasping, opening, and closing.

This demonstrates that collision-free navigation to a work pose does not guarantee that the complete manipulation task is feasible from that pose.

## Final Result

- Selected route: `navigate_to_microwave_backup_right`
- Result: PASS
- States: 504
- Actions: 11
- Checked environment geoms: 96
- Maximum door angle: `1.0 rad`
- Final door angle: `0.0 rad`
- Visual-overlap failures: 0
- Forbidden-contact failures: 0
- Grasp-loss failures: 0
- Maximum adjacent arm-joint step: `0.0760742 rad`
- Front and top-view frames: 169 each

Both videos were inspected. The top view shows the robot moving around the red obstacle, with no visible penetration during the complete task.

## Current Boundary

This is candidate-route validation with fallback, not global planning based on A*, RRT, or a navigation mesh. Candidate offsets and detour points are supplied by the configuration. The program transforms coordinates, generates trajectories, validates every state, and selects the first safe candidate.
