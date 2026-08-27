data = {
    "robots": [
        {"name": "R1", "fps": 30},
        {"name": "R2", "fps": 60}
    ]
}
import json 
with open("/home/users/dazhi.sun-labs/projects/robot.json","w") as f:
    json.dump(data,f)