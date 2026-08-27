# Week 4 Plan

## Objective

Build a reproducible path from a generated SceneSmith room to a validated,
browser-viewable scene containing an articulated Articraft object.

## Phase 1: Stabilize Floor-Plan Generation

**Goal:** Run only the SceneSmith floor-plan stage without requiring unrelated
asset-generation services.

- [x] Restore the damaged pipeline file and pass Python syntax checks.
- [x] Skip geometry, HSSD, Objaverse, ArtVIP, and material servers when both
  `start_stage` and `stop_stage` are `floor_plan`.
- [x] Generate floor-plan artifacts.
- [x] Export the Blender result to GLB.
- [x] Display the GLB in a browser viewer.

## Phase 2: Build a Complete Static Scene

**Goal:** Combine the existing room and furniture without regenerating assets.

- [x] Read the saved furniture placement state.
- [x] Load seven existing furniture GLBs.
- [x] Combine room structure and furniture in Blender.
- [x] Export a complete GLB and BLEND file.
- [x] Check grounding, room bounds, collisions, and accessibility.
- [x] Freeze the result as `stable_scene_v1`.

## Phase 3: Integrate an Articulated Object

**Goal:** Add an existing Articraft microwave while preserving articulation.

- [x] Parse the source URDF.
- [x] Rebuild links, visual geometry, and joints in Blender.
- [x] Place the microwave on the existing study desk.
- [x] Export joint metadata to GLB.
- [x] Add Three.js joint controls.
- [x] Validate closed, open, and sampled motion states.
- [x] Freeze the result as `stable_scene_v1_plus_microwave_v1`.

## Acceptance Criteria

- [x] No new room, furniture, or articulated asset is generated during freeze.
- [x] The base stable version remains unchanged.
- [x] The complete GLB contains room structure, seven furniture assets, and the
  microwave.
- [x] Five microwave joints remain discoverable in the browser.
- [x] The validated operation path has no unintended collision.
- [x] Scene accessibility remains above 0.99.
- [x] Reports, screenshots, and SHA-256 manifests are saved.

## Phase 4: Scale to Multiple Articulated Objects

**Goal:** Demonstrate that the integration works for more than one URDF asset.

- [x] Reuse a separate static reading-room scene.
- [x] Align an Articraft single door with the existing entrance opening.
- [x] Place an Articraft double-door cabinet against a free wall.
- [x] Keep the articulated microwave supported by the writing desk.
- [x] Namespace links and joints for multiple assets.
- [x] Expose eight browser controls.
- [x] Sample 23 valid motion poses.
- [x] Verify 0 new self, furniture, inter-asset, and room-bound collisions.
- [x] Verify reachability of four required interaction areas.
- [x] Freeze `articulated_demo_room_v1` with reports and checksums.
