observation = {"robot_position":0, "cabinet_position":5, "hinge_position":5,"door_angle":0, "Has Grabbed Handle": False}
target_angle = 80
actions = ["move_to_cabinet", "grab_handle", "pull_door", "stop"]

def policy(observation):
    if observation["robot_position"] < observation["cabinet_position"]:
        return actions[0]
    elif observation["Has Grabbed Handle"] == False:
        return actions[1]
    elif observation["door_angle"] < target_angle:
        return actions[2]
    else:
        return actions[3]

def step(observation, action):
    if action == actions[0]:
        observation["robot_position"] += 1
    elif action == actions[1]:
        observation["Has Grabbed Handle"] = True
    elif action == actions[2]:
        observation["door_angle"] += 20
    else:
        pass
    return observation

for step_id in range(20):
    print(step_id)
    action = policy(observation)
    print("action:", action)
    observation = step(observation, action)
    print("observation:", observation)
    if observation["door_angle"] >= target_angle:
        print("let's go!")
        break