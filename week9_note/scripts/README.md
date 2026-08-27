# Week9 runner

`run_articulated_task.py` is the shared Week9/Week10 runner. It:

1. loads one YAML task and its MuJoCo scene;
2. binds object-joint aliases to `TaskState`;
3. executes the reusable action registry;
4. validates every state for Panda/environment overlap, forbidden target
   contact, grasp retention, target attainment, restoration, and joint-step
   continuity;
5. writes the trajectory and summary; and
6. renders front and top-view GIFs unless `--skip-render` is supplied.

The prismatic grasp-follow action and scene runtime live in
`week9_note/task_system/` and are imported unchanged by Week10.
