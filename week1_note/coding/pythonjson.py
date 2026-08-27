import json

with open("config.json","r") as f:
    data=json.load(f)

print(data["robot"]["name"])
print(data["robot"]["battery"])

for value in data["robot"]["sensors"].values():
    print(value)
