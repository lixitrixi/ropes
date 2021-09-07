class Point():
    def __init__(self, pos, locked): # pos = (x, y); locked = bool
        self.pos = pos
        self.prev_pos = pos
        self.locked = locked
        self.is_new = True # this point is currently being created; don't apply physics to it
        self.sticks = []

class Stick():
    def __init__(self, pointA, pointB, length):
        self.pointA = pointA
        self.pointB = pointB
        self.length = length
        pointA.sticks.append(self)
        pointB.sticks.append(self)
    
    def get_center(self):
        return ((self.pointA.pos[0]+self.pointB.pos[0])/2, (self.pointA.pos[1]+self.pointB.pos[1])/2)
    
    def get_stress(self):
        return distance(self.pointA.pos, self.pointB.pos)-self.length
    
    def get_stress_color(self): # returns an RGB color based on the current stress of the stick
        return (min(max(30+self.get_stress()*(255-30)/MAX_STRESS, 0), 255), min(max(120-self.get_stress()*8, 0), 255), 50)


class Game():
    def __init__(self, points=[], sticks=[]):
        self.points = points
        self.sticks = sticks

    def update(self, d_time): # d_time = time since last frame (IN SECONDS)
        d_time = max(d_time, 0.01)
        for p in self.points:
            if not p.locked and not p.is_new:
                pos_before_update = p.pos
                p.pos = (2*p.pos[0]-p.prev_pos[0], 2*p.pos[1]-p.prev_pos[1])
                p.pos = (p.pos[0]+ACC_X*(d_time**2), p.pos[1]+ACC_Y*(d_time**2))
                p.prev_pos = pos_before_update
        
        for stick in self.sticks:
            if USE_STRESS and stick.get_stress() > MAX_STRESS:
                self.sticks.remove(stick)
            stick_center = stick.get_center()
            dist = distance(stick.pointA.pos, stick.pointB.pos)
            stick_dir = ((stick.pointA.pos[0]-stick.pointB.pos[0])/dist, (stick.pointA.pos[1]-stick.pointB.pos[1])/dist)
            if not stick.pointA.locked:
                stick.pointA.pos = (stick_center[0]+stick_dir[0]*stick.length/2, stick_center[1]+stick_dir[1]*stick.length/2)
            if not stick.pointB.locked:
                stick.pointB.pos = (stick_center[0]-stick_dir[0]*stick.length/2, stick_center[1]-stick_dir[1]*stick.length/2)
