# Week 11: Complex Articulated-Object Tasks

This directory contains four transfer-task prototypes and two validated multi-mechanism tasks. The tasks combine mobile-base navigation, target approach, two-finger grasping, articulated-object manipulation, target switching, and final restoration. All six scenes now also include explicit structural connections and internal supports.

## Current Status

The reported cross-scene defect was primarily structural: generated frame members, hinge parts, handles, rails, modules, and stored items were positioned without an explicit visible connection or support. All six scenes were repaired with grounding plinths, frame connectors, hinge or rail mounts, handle brackets, and internal object supports. The structural audit now passes **118 / 118 checks**.

The original four transfer scripts reach their configured joint and position goals and no longer contain unsupported initial/final placements. They are still retained as motion-sequence prototypes because their kinematic payload transport and original validation do not establish complete collision or dynamic validity.

The industrial-printer task models the service panel and toner tray as two constrained articulated mechanisms, places the cartridge on the tray and the tray on a continuous collision-enabled guide rail, and passes the expanded validation suite across all 942 states.

The industrial-sterilizer task increases the difficulty to three mechanisms and three grasp targets. The robot must unlock a guided and visibly connected safety latch before opening the panel, operate and restore the supported internal instrument tray, close the panel, and then regrasp and relock the latch. It passes the same expanded validation across all 1,487 states.

See [WEEK11_ISSUE_REPORT.md](WEEK11_ISSUE_REPORT.md) for the complete investigation.

## Scenes and Tasks

| Scene | Complete task | Mechanisms | Actions | States | Current status |
|---|---|---:|---:|---:|---|
| Pantry | Open a refrigerator and a cupboard, then transfer a food can from the refrigerator to the cupboard | 2 hinges | 24 | 1,139 | Structural PASS; motion prototype |
| Workshop | Pull out a tool drawer, open a safety locker, and transfer a tool from the drawer to the locker | 1 slide + 1 hinge | 24 | 1,210 | Structural PASS; motion prototype |
| Laundry room | Open a washer and a dryer, then transfer laundry from the washer to the dryer | 2 hinges | 24 | 1,139 | Structural PASS; motion prototype |
| Laboratory | Open an incubator, pull out its internal tray, open cold storage, and transfer a sample to cold storage | 1 slide + 2 hinges | 31 | 1,457 | Structural PASS; motion prototype |
| Industrial printer | Open a service panel, pull out and inspect the internal toner tray, restore the tray, and close the panel | 1 hinge + 1 slide | 24 | 942 | Structural + strict validation PASS |
| Industrial sterilizer | Unlock the safety latch, open the service panel, pull out and restore the instrument tray, close the panel, and relock the latch | 1 hinge + 2 slides | 38 | 1,487 | Structural + strict validation PASS |

## Task Complexity

- Each sequence combines navigation, approach, two-finger grasping, articulated manipulation, release, obstacle-aware repositioning, target switching, and retreat.
- The four transfer prototypes also include item retrieval, transport, and placement.
- The printer task requires two separate grasps of the service panel with a complete toner-tray operation between them.
- The sterilizer task adds a safety interlock, a third target, two additional regrasp cycles, and a required unlock-operate-close-relock order.
- The structural evaluator checks 118 grounding, attachment, and support relationships across all six scenes, including full-trajectory rail and linkage checks.
- The expanded printer and sterilizer evaluator checks every state for robot-environment overlap, mechanism clearance, grasp continuity, collision-enabled visual geometry, tray support, arm-joint continuity, and final mechanism restoration.

The four transfer-prototype checks do not establish full physical validity. The two accepted tasks explicitly cover their complete mechanism and support geometry, but they remain kinematic articulated-object demonstrations rather than force-controlled dynamics experiments.

## Running a Task

Run either accepted task from the project root:

```bash
scenesmith/.mujoco_venv/bin/python -m week11_note.scripts.run_validated_articulated_task \
  --config week11_note/configs/printer_service_panel_tray_restore.yaml

scenesmith/.mujoco_venv/bin/python -m week11_note.scripts.run_validated_articulated_task \
  --config week11_note/configs/sterilizer_safety_latch_panel_tray_reset.yaml
```

Add `--skip-render` to execute trajectory generation and validation without regenerating the GIFs. The original transfer prototypes still use `week11_note.scripts.run_complex_task`.

Run the cross-scene structural audit with:

```bash
scenesmith/.mujoco_venv/bin/python -m week11_note.scripts.audit_structural_support
```

## Directory Layout

- `xml/`: six MuJoCo scenes.
- `configs/`: action sequences, goal states, runtime bindings, and rendering parameters.
- `task_system/`: the Week 11 runtime and payload-transfer action.
- `scripts/`: transfer-task, strict articulated-task, structural-audit, and review-image entry points.
- `assets/`: front-view and top-view GIFs for every task.
- `results/`: full trajectory files and evaluation summaries.

See [COMPLEX_TASK_REPORT.md](COMPLEX_TASK_REPORT.md) for the task summary and [WEEK11_ISSUE_REPORT.md](WEEK11_ISSUE_REPORT.md) for the structural repair assessment.

The work log for this repair is recorded in [DAILY_RECORD.md](DAILY_RECORD.md).
