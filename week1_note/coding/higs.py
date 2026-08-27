import json

with open("/home/users/dazhi.sun-labs/projects/data.json", "r") as f:
    data = json.load(f)

total = 0
max1 = 0
min1 = data["robots"][0]["fps"]

for robot in data["robots"]:
    print(robot["name"])
    total += robot["fps"]

    if robot["fps"] >= max1:
        max1 = robot["fps"]

    if robot["fps"] <= min1:
        min1 = robot["fps"]

print(total / len(data["robots"]))
print(max1, min1)