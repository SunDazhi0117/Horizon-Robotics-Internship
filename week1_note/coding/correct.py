import os
import json

print(os.getcwd())

with open("data.json", "r") as f:
    data = json.load(f)

print(data)