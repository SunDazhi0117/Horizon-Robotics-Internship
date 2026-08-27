observation = {"robot_position":0, "cabinet_position":5, "hinge_position":5, "door_angle":0}
target_angle = 80
actions = ["move_to_cabinet", "grab_handle", "pull_door", "stop"]

def policy(observation):
    if observation["robot_position"] < observation["cabinet_position"]:
        return actions[0]
    elif observation["door_angle"] < target_angle:
        return actions[2]
    else:
        return actions[3]

def step(observation, action):
    if action == actions[0]:
        observation["robot_position"] += 1
    elif action == actions[2]:
        observation["door_angle"] += 20
    elif action == actions[3]:
        pass
    return observation

for step_id in range(20):
    print("Step:", step_id)
    action = policy(observation)
    print("Action:", action)
    observation = step(observation, action)
    print("Observation:", observation)
    if observation["door_angle"] >= target_angle:
        print("Task Success!")
        break
