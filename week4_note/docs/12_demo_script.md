# One-Minute Demo Script

Week 4 built a reproducible path from generated indoor geometry to interactive
3D scenes. SceneSmith supplies room layout, static furniture, and placement
state. Articraft supplies URDF links, joint types, axes, and limits.

After freezing `stable_scene_v1`,
`stable_scene_v1_plus_microwave_v1` added a microwave while preserving five
joints, including a door range from zero to `1.75 radians`. The latest reading
room contains an entry door, double-door cabinet, and microwave:
three articulated objects and eight joints.

Across 23 sampled accepted motion states, I found no new self, furniture, or
inter-object collisions. Four out of four operation regions were reachable.
The viewer is Ready, all eight controllers work, and Reset restores the rest
poses.

This is interactive because joints remain controllable after integration. It
is not a robot task suite: there is no controller, policy, grasping, or
dynamics evaluation. Week 5–8 will draft and later implement tasks such as
opening doors and safely extending the microwave tray.

## Accuracy Notes

- Say **sampled accepted motion states**, not universal collision-free motion.
- Say **interactive 3D scene**, not robot simulation.
- Say Week 5–8 tasks are drafts until a controller and evaluation system exist.
