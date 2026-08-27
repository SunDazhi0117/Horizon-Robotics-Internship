# Week9 task configs

- `sliding_window_open_close.yaml`: the simplest demonstration and the first
  use of the reusable `follow_slide_joint` action.
- `storage_box_open_close.yaml`: changes the articulation to a horizontal
  hinge and coordinates the mobile base with the rising lid.

Each config contains the model path, object-joint aliases, permitted finger
targets, initial state, ordered actions, numerical acceptance goals, and two
fixed render cameras.
