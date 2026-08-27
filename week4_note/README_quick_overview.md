# Week 4 Quick Project Overview

Week 4 completed a small, reproducible 3D-scene workflow instead of attempting to install every research-stage SceneSmith dependency.

The workflow can:

1. Generate an indoor floor plan with SceneSmith.
2. Combine room geometry with seven static furniture assets.
3. export a browser-ready GLB through background Blender execution.
4. Place an Articraft URDF microwave on a scene work surface.
5. Preserve five microwave joints and control them in a Three.js viewer.
6. Scale to an entry door, double-door cabinet, and microwave with eight joints.
7. Check navigation clearance with an inflated 2D occupancy grid.
8. Freeze stable versions with acceptance reports and SHA-256 manifests.

## Accepted Results

- `stable_scene_v1`: seven static furniture assets.
- `stable_scene_v1_plus_microwave_v1`: seven static furniture assets and one five-joint microwave.
- `articulated_demo_room_v1`: six static furniture assets and three articulated objects with eight joints.
- Across 23 sampled poses, new self, furniture, and inter-object collision counts were all zero.
- The central area, microwave, cabinet, and reading area were reachable from the open entrance: 4/4 passed.
- All eight browser controls and Reset worked.

This is an interactive 3D-scene integration with lightweight validation. It is not a robot task suite, robot controller, or complete dynamics simulation.

[Watch the 13.6-second articulated scene demo](assets/week4_articulated_scene_demo.mp4)

## Workflow

```text
Text description
  -> SceneSmith room generation
  -> furniture generation and placement
  -> Blender scene assembly
  -> GLB export
  -> Articraft URDF converted to a Blender joint hierarchy
  -> separate namespaces for articulated objects
  -> entry door, cabinet, and microwave integration
  -> Three.js visualization and controls
  -> collision, accessibility, and browser checks
  -> frozen stable version
```

The main engineering shift was from asking whether a model could be generated to asking whether its output could be assembled, displayed, validated, and reproduced.

## Known Limitation

The microwave door and tray cannot move safely in every order. The door must first open to at least `1.50 rad`; extending the tray beyond approximately `0.11 m` while the door is closed causes an intersection. The viewer therefore locks the tray below `1.50 rad` and retracts it before closing the door.

See [the main README](README.md) and [`docs/`](docs/) for the complete record.

Run these checks:

```bash
python scripts/check_week4_note.py
python scripts/scene_summary.py
```
