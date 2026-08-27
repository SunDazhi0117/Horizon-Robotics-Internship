# Resume Bullet Drafts

Use only the bullets that match the role and space available.

## Concise Version

- Built an agent-assisted SceneSmith-to-Three.js pipeline that assembled room
  geometry and seven generated furniture assets into a reproducible GLB scene.
- Integrated an Articraft URDF microwave into a SceneSmith room while
  preserving five revolute, prismatic, and continuous joints for interactive
  browser control.
- Implemented AABB/BVH placement and collision checks across sampled
  articulated poses, finding zero unintended collisions along the validated
  door-then-tray operation path.
- Evaluated navigation clearance with an inflated 2D occupancy grid, achieving
  99.688% connected coverage in the first stable scene against a 99%
  acceptance threshold.
- Added browser smoke tests, human-readable acceptance reports, and SHA-256
  manifests to freeze validated scene versions without modifying prior
  outputs.
- Scaled the pipeline to three articulated URDF assets and eight browser-driven
  joints, validating 23 sampled poses with zero new self, furniture,
  inter-asset, or room-bound collisions.

## Recommended Internship Version

- Built an agent-assisted SceneSmith-to-Three.js pipeline that assembled
  generated room geometry, static furniture, and Articraft URDF assets into
  reproducible interactive GLB scenes.
- Scaled the integration to an articulated entry door, double-door cabinet,
  and microwave, preserving eight browser-driven revolute, prismatic, and
  continuous joints.
- Implemented sampled AABB/BVH collision checks, interaction-target
  reachability checks, browser smoke tests, acceptance reports, and SHA-256
  manifests; validated 23 accepted poses with no new collisions.

## Single-Bullet Version

- Developed an agent-assisted SceneSmith + Articraft pipeline that integrated
  static furniture with an articulated entry door, double-door cabinet, and
  microwave in an interactive Three.js scene, preserving eight joints and
  validating 23 sampled poses with no new collisions on accepted paths.

## Interview Talking Points

- Explain why floor-plan-only execution should not initialize asset services.
- Describe how `scene_state.json` transforms reconstruct furniture placement.
- Compare the roles of URDF, SDF, BLEND, and GLB.
- Explain how joint metadata survives from URDF to a browser control.
- Discuss the door-tray collision and why joint limits alone are insufficient.
- Explain why immutable versions and checksums matter for generated assets.
- Be precise that this is an interactive 3D scene workflow with lightweight
  validation, not yet a full dynamics simulation.
