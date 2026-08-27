import torch
import torch.nn as nn

# Observation:
# [battery, robot_x, robot_y]
observation = torch.tensor([20.0, 3.0, 5.0])

# A very simple policy model
# Input: 3 numbers
# Output: 1 action score
model = nn.Linear(
    in_features=3,
    out_features=1
)

action_score = model(observation)

print("observation:", observation)
print("observation shape:", observation.shape)
print("model:", model)
print("action score:", action_score)