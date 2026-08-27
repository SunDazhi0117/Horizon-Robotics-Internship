
with open("scored.txt","r") as f:
    higgs=f.readlines()
total=0
passman=0
fail=0

for item in higgs:
    total+=int(item.strip())
for item in higgs:
    if int(item.strip())>=60:
        passman+=1
    else:
        fail+=1
print(total/len(higgs),passman,fail)

