# Fast Preview Mode

The fast preview path reduces iteration time without changing SceneSmith's
default generation settings or any existing output.

Run:

```bash
scripts/run_static_reading_room_fast.sh
```

The preview preset uses:

- the GPU with the most free memory;
- Hunyuan3D Mini in shape-only mode;
- five Hunyuan inference steps, unchanged from the normal local workflow;
- octree resolution 128 instead of 256;
- two physics-analysis side views instead of four;
- four validation TAA samples instead of eight;
- no asset retries, critique rounds, projection, or SceneEval export.

The geometry server can run one worker per selected GPU. Hunyuan3D workers
preload in parallel, while SAM3D workers retain serialized preload because
their much larger checkpoints can create severe disk contention.

Fast preview defaults to one GPU because Hunyuan3D Mini preload is expensive
relative to a small six- or seven-asset room. Use multiple workers for larger
batches or full-resolution generation:

```bash
SCENESMITH_GPU_WORKERS=4 scripts/run_static_reading_room_fast.sh
```

## Quality Tradeoff

Resolution 128 is intended for layout and workflow iteration. Use the normal
script for an accepted final asset:

```bash
scripts/run_static_reading_room.sh
```

The fast mode can be customized without editing code:

```bash
SCENESMITH_GPU_WORKERS=2 \
SCENESMITH_HUNYUAN_OCTREE_RESOLUTION=192 \
SCENESMITH_PHYSICS_SIDE_VIEWS=4 \
scripts/run_static_reading_room_fast.sh
```

An existing `CUDA_VISIBLE_DEVICES` value always takes precedence over automatic
GPU selection.

## Local Geometry Benchmark

Using the existing study-desk reference image on one RTX 4090, after model
preload:

| Octree resolution | Generation time |
| --- | ---: |
| 256 | 37.256 s |
| 128 | 9.818 s |

For that input, resolution 128 reduced raw geometry time by 73.6% (3.79x).
This is not an end-to-end scene benchmark: agent calls, model preload, Blender
conversion, collision decomposition, and validation still add time.

A four-worker Hunyuan3D Mini preload completed in 181.12 seconds with all
workers loading concurrently. This confirms multi-GPU startup works, but also
shows why one worker is the better default for a small preview batch.
