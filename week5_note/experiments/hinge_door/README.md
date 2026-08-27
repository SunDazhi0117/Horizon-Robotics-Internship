# Week5 MuJoCo Test: Hinge Door

This is a minimal MuJoCo exercise for understanding articulated objects.

It contains:

- floor
- wall / door frame
- one door body
- one hinge joint
- one position actuator
- Python simulation loop
- GIF rendering
- PASS / FAIL based on door joint angle

Run from the SceneSmith project environment:

```bash
cd /home/users/dazhi.sun-labs/projects/scenesmith
source .mujoco_venv/bin/activate
python /home/users/dazhi.sun-labs/projects/week5_note/experiments/hinge_door/run_hinge_door.py
```

Success condition:

```text
door_hinge qpos > 1.2 rad
```
