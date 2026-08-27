import json

from robot import Robot

with open("/home/users/dazhi.sun-labs/projects/robot_project/config.json", "r") as f:
    res = json.load(f)

robot_family=[]
robot_family = []

for robot_data in res["robots"]:

    robot = Robot(
        robot_data["name"],
        robot_data["battery"]
    )

    robot_family.append(robot)

for robot in robot_family:
    robot.info()


for robot in robot_family:
    robot.move()
    robot.info()