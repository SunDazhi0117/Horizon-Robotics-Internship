class Robot:
    def __init__(self,name,battery):
        self.name=name
        self.battery=battery
    
    def move(self):
        self.battery-=10
    
    def info(self):
        print("name:", self.name)
        print("battery:", self.battery)

    def charge(self):
        self.battery+=10
r = Robot("robot1", 100)

r.info()

r.move()
r.move()

r.info()

r.charge()

r.info()


