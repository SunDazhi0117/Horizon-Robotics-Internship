# Week 4 Completion Checklist

This checklist compares the original Week 4 plan with the evidence produced
during the SceneSmith and Articraft work. It separates completed engineering
work from lightweight validation and future robot tasks.

## 1. Learn Basic Scene Construction

**Original plan**

Understand how an indoor scene is represented and assembled, including floors,
walls, windows, furniture assets, transforms, and export formats.

**Current result**

The workflow now distinguishes room geometry, individual furniture GLBs,
`scene_state.json` placement data, editable BLEND files, browser-oriented GLB
files, and URDF/SDF representations.

**Evidence**

- SceneSmith floor-plan output and room geometry were inspected.
- A room containing a floor, walls, windows, and seven furniture assets was
  assembled into one GLB and BLEND file.
- The role of `scene_state.json` and coordinate transforms is documented in
  `02_workflow_understanding.md`.

**Status: Completed**

## 2. Use an Agent to Assist Indoor Scene Generation

**Original plan**

Use an agent-assisted workflow to create and debug a simple indoor scene.

**Current result**

The agent-assisted workflow was used to isolate SceneSmith stages, run the
floor-plan and furniture workflow, assemble outputs, debug viewers, write
validation scripts, and produce acceptance reports. The agent did not replace
SceneSmith or Articraft; it orchestrated tools, edited code, and verified
outputs.

**Evidence**

- Floor-plan-only service gating was implemented and tested.
- Static room and furniture outputs were exported to browser-viewable GLB.
- Sanitized task prompts and human/agent responsibilities are recorded in
  `07_agent_prompts.md`.

**Status: Completed**

## 3. Place an Articulated Object in a Scene

**Original plan**

Place at least one Articraft articulated object into a SceneSmith room while
retaining its motion structure.

**Current result**

An Articraft microwave was placed on the study desk in
`stable_scene_v1_plus_microwave_v1`. Its five joints remain discoverable and
controllable in the browser.

**Evidence**

- 1 articulated microwave.
- 5 preserved joints.
- Revolute, prismatic, and continuous joint types.
- Microwave door range: `0` to `1.75 rad`.
- Viewer controls and Reset passed the browser smoke test.
- Door-tray interlock passed locked, unlocked, and auto-retract tests.

**Status: Completed**

## 4. Check Physical Reasonableness

**Original plan**

Check whether objects are grounded, inside room bounds, reachable, and free
from obvious collision during interaction.

**Current result**

Lightweight validation covers support contact, transformed bounds, AABB/BVH
collision checks, sampled joint poses, and an inflated 2D occupancy grid. It
does not include dynamics, forces, torque, grasping, or a full robot model.

**Evidence**

- Static scene furniture collision count: 0.
- Microwave closed/open and valid door-then-tray sequence: PASS.
- Multi-articulated scene: 23 sampled poses.
- New self, furniture, inter-asset, and room-bound collisions: 0 on accepted
  paths.
- Four required operation regions are reachable.
- Known invalid sequence is documented: extending the microwave tray beyond
  approximately `0.11 m` while its door is closed.
- The Viewer now prevents that sequence with a `1.50 rad` interlock.

**Status: Partially Completed**

Full physical simulation remains future work.

## 5. Organize Scene Configuration and Loading Scripts

**Original plan**

Make scene assembly, export, loading, validation, and viewing reproducible
instead of relying on manual Blender operations.

**Current result**

The local workflow includes scripts for floor-plan export, complete-room
assembly, multi-URDF assembly, validation, viewer serving, browser checks, and
stable-version checksums.

**Evidence**

- Saved `scene_state.json` placement inputs.
- Repeatable BLEND-to-GLB export.
- Multi-URDF assembler with per-asset namespaces.
- Machine-readable JSON and human-readable acceptance reports.
- Three.js viewer with metadata-driven joint controls.
- SHA-256 manifests for frozen scene outputs.

**Status: Completed**

## 6. Include Two to Three Interactive Objects

**Original plan**

Create a scene containing two or three objects that retain interactive joint
behavior.

**Current result**

`articulated_demo_room_v1` contains three articulated objects:

1. Entry door: 1 revolute joint.
2. Double-door cabinet: 2 revolute joints.
3. Microwave: 5 mixed joints.

**Evidence**

- 3 articulated objects.
- 8 total joints.
- 8 browser controls.
- All 8 transforms changed during the browser test.
- Reset restored all rest poses.

**Status: Completed**

## 7. Robot Tasks

**Original plan**

Robot interaction and task execution were intended for a later stage, not as a
Week 4 acceptance requirement.

**Current result**

No robot, controller, planner, grasp, policy, or task benchmark was implemented
in Week 4. The current outputs are interactive scene demos and validation
artifacts.

**Evidence**

- README scope explicitly excludes a robot task suite.
- Current controls are human-operated Three.js joint sliders.
- `11_week5_task_suite_draft.md` describes future tasks without claiming
  implementation.

**Status: Planned for Next Stage**

Robot task work is reserved for Week 5–8.

## Overall Week 4 Status

Week 4 achieved the intended scene-generation, scene-assembly, articulated
integration, browser-viewing, and documentation goals. Physical reasonableness
was checked at a lightweight geometric level. Robot task execution remains a
clearly separated future stage.
