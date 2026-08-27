# Lessons and Next Steps

## Lessons Learned

### A Smaller Pipeline Can Be More Useful

Running only the required stage made SceneSmith testable before every research
dependency was available. A partial pipeline with clear boundaries was more
useful than an unstable full run.

### Saved State Is as Important as Generated Geometry

Furniture GLBs alone were not enough to reconstruct the room. The scene state
provided the transforms and semantic identities needed to assemble the final
scene.

### Visual Success Is Not Physical Success

The microwave looked correct in a closed screenshot, but motion sampling found
an invalid door-tray sequence. Validation must include trajectories, not only
rest poses.

### Joint Limits Are Not Task Constraints

Each microwave joint has a valid individual range, but combinations of valid
joint values can still collide. Cross-joint constraints need a state machine,
interlock, planner, or physics-aware controller.

### Multi-Object Integration Needs Namespaces

One URDF can use simple node names, but several URDF files may reuse names such
as `door`, `frame`, or `hinge`. Per-asset namespaces make Blender parenting,
GLB metadata, browser controls, and collision reports unambiguous.

### Stable Outputs Need Evidence

The acceptance report, JSON measurements, browser test, screenshots, and
checksums are part of the result. They make the scene easier to review and
reduce ambiguity about what was actually tested.

## Current Limitations

- Collision checks are lightweight and do not replace full physics simulation.
- Accessibility uses inflated 2D bounds rather than a full robot model.
- Some generated furniture has unrealistic proportions.
- The viewer enforces the microwave door-tray interlock, but does not yet model
  broader cross-object task coordination.
- Large model assets are local and are not included in this notes repository.

## Next Steps

1. Verify the door-tray interlock again when a physics/controller layer exists.
2. Export the complete articulated scene to a simulation format.
3. Test the microwave with Drake, MuJoCo, or another physics engine.
4. Add a robot and verify an approach-and-open task.
5. Replace AABB-only furniture checks with mesh-level collision geometry.
6. Add a single command that rebuilds, validates, and serves a selected scene.
7. Record a short browser demo for the GitHub project page.
8. Add coordinated task sequences across the entry door, cabinet, and
   microwave instead of controlling every joint independently.
