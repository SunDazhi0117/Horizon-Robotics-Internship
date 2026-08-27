# Local Reproducible Workflow

## Known Good Run

Repository:

```text
/home/users/dazhi.sun-labs/projects/scenesmith
```

Reference output:

```text
outputs/2026-06-29/17-55-56
```

The reference run contains:

- `scene_000/final_floor_plan/floor_plan.png`
- `scene_000/floor_plans/final_floor_plan/floor_plan.blend`
- `scene_000/floor_plans/final_floor_plan/floor_plan.dmd.yaml`
- `scene_000/room_geometry/room_geometry_studio.sdf`
- `scene_000/floor_plan_export.glb`

## Commands

Export the floor plan from Blender to GLB without opening the Blender GUI:

```bash
scripts/export_floor_plan_glb.sh
```

Check all required outputs and parse the exported GLB:

```bash
scripts/check_scenesmith_outputs.sh
```

Start the local Three.js viewer:

```bash
scripts/serve_glb_viewer.sh
```

Each command accepts a different run directory as its first argument:

```bash
scripts/export_floor_plan_glb.sh outputs/YYYY-MM-DD/HH-MM-SS
scripts/check_scenesmith_outputs.sh outputs/YYYY-MM-DD/HH-MM-SS
scripts/serve_glb_viewer.sh outputs/YYYY-MM-DD/HH-MM-SS 8080
```

## Python Environments

Always use the project-specific interpreter:

```text
SceneSmith: /home/users/dazhi.sun-labs/projects/scenesmith/.venv/bin/python
Articraft:  /home/users/dazhi.sun-labs/projects/articraft/.venv/bin/python
```

Do not rely on the shell `python`. It currently points to a separate Python
3.13 installation.

The SceneSmith environment is healthy and includes Python 3.11, PyTorch,
Drake, and Blender Python. The Articraft environment is separate and currently
does not include `pip`; that does not affect SceneSmith.

## Pipeline Status

SceneSmith runs these stages:

1. `floor_plan`
2. `furniture`
3. `wall_mounted`
4. `ceiling_mounted`
5. `manipuland`

`floor_plan` is working with the Codex CLI provider. The next `furniture`
stage is currently blocked by its configured asset source, not by Python,
PyTorch, Drake, or Blender.

The default furniture asset source is SAM3D. The following inputs are missing:

- Python modules: `sam3`, `sam3d_objects`, `pytorch3d`, `kaolin`, `gsplat`,
  `nvdiffrast`
- Checkpoints: `external/checkpoints/sam3.pt`,
  `external/checkpoints/pipeline.yaml`
- ArtVIP content under `data/artvip_sdf`

Alternative asset sources are also unavailable:

- HSSD: `data/hssd-models`, `data/preprocessed`
- Objaverse: `data/objathor-assets`
- Materials retrieval content: `data/materials`

Do not start the furniture stage until one asset source is intentionally
selected and prepared. A future Articraft-backed asset source could avoid
installing every original SceneSmith dataset.

