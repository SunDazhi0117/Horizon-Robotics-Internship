# Technical Principles

## Stage Gating and Dependency Isolation

A pipeline stage should initialize only the services it needs. This reduces
startup time, avoids unrelated failure modes, and makes partial workflows
testable. The floor-plan-only run does not need SAM3D, ArtVIP, HSSD, Objaverse,
or material retrieval.

## Representation Boundaries

Different formats serve different purposes:

| Format | Role |
| --- | --- |
| PNG | Rendered preview for fast visual inspection |
| GLTF + BIN | Split room geometry and binary mesh buffers |
| DMD YAML | Structured scene and floor-plan description |
| SDF | Simulation-oriented scene representation |
| URDF | Articulated link and joint structure |
| BLEND | Editable assembly source |
| GLB | Portable geometry, hierarchy, materials, and metadata |
| JSON | Placement state, validation output, and reproducibility metadata |

No single format is best for every stage. The workflow succeeds by preserving
the right information while crossing these boundaries.

## Coordinate Frames

Placement requires more than copying XYZ values. The implementation must
account for:

- local versus world coordinates;
- quaternion ordering;
- object-facing direction;
- Blender versus Three.js axis conventions;
- support surface height;
- transformed bounding boxes.

The microwave root is aligned to the desk orientation, placed at the desk's
top height, and rotated so its front faces into the room.

## Articulation

The microwave contains three joint categories:

- **Revolute:** bounded door rotation.
- **Prismatic:** bounded tray translation.
- **Continuous:** unbounded turntable and knob rotation.

A joint is defined by more than its type. Its parent, child, origin, axis, and
limits must all remain consistent through URDF parsing, Blender parenting, GLB
export, and viewer control.

When multiple URDF files share a scene, each hierarchy also needs a stable
asset namespace. Namespacing prevents common names such as `door`, `frame`, or
`hinge` from overwriting one another and keeps validation results attributable
to the correct object.

## Collision Checking

Two levels of lightweight checks are useful:

1. **AABB checks** quickly detect furniture overlap and room-bound violations.
2. **BVH mesh checks** sample articulated states and detect geometry
   intersections more precisely.

Expected contact between directly connected parts is classified separately
from unintended collision. Otherwise, a hinge or a turntable resting on its
tray would be incorrectly reported as a failure.

## Accessibility

Accessibility is evaluated using a 2D occupancy grid:

1. Project furniture bounds onto the floor.
2. Inflate obstacles by the robot radius.
3. Select a free entrance cell.
4. Run flood fill through free cells.
5. Divide reachable free cells by all free cells.

The microwave does not reduce floor accessibility because its footprint is
fully contained by the existing desk footprint and it is elevated on the desk.

## Kinematic Validation Versus Dynamic Simulation

Loading a URDF, moving its joints, and checking collision geometry is a
kinematic validation. It confirms that the hierarchy, axes, limits, and sampled
poses are internally usable.

Dynamic simulation additionally requires physically valid mass and inertia for
every moving link. The current Articraft microwave URDF has no `inertial`
blocks. Drake can parse it and evaluate kinematic collision states, but it
cannot advance dynamics because the turntable's mass matrix is not
positive-definite. Week 4 therefore claims browser interaction and sampled
kinematic validation, not physically validated microwave dynamics.

## Reproducibility

A generated result is not stable merely because it looks correct once.
A stable result should include:

- source references;
- deterministic assembly inputs;
- exported artifacts;
- machine-readable validation output;
- a human-readable acceptance report;
- browser smoke-test results;
- SHA-256 checksums.

This turns an experiment into a reviewable engineering artifact.
