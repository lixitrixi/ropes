# Imports
import pygame
from pygame.locals import *
import sys, math


# Vars
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

ACC_X = 0 # global x acceleration
ACC_Y = 500 # global y acceleration

USE_STRESS = False
MAX_STRESS = 4.5

GRID_SIZE = 25 # size (in pixels) of the snapping grid
SNAP_RADIUS = 20 # within this distance, a stick will snap to the nearest point while being created
DELETE_RADIUS = 10

POINT_RADIUS = 7
STICK_WIDTH = 7

white = (255, 255, 255)
bg_color = (65, 65, 130)
point_preview_color = (85, 85, 160)
point_color = (255, 255, 255)
shadow_color = (0, 0, 0)
locked_point_color = (255, 75, 75)
deleting_color = (255, 105, 105)


# Classes
class Point():
    def __init__(self, pos, locked=False, is_new=True): # pos = (x, y); locked = bool
        self.pos = pos
        self.prev_pos = pos
        self.locked = locked
        self.is_new = is_new # this point is currently being created; don't apply physics to it
        self.sticks = []

class Stick():
    def __init__(self, pointA, pointB):
        self.pointA = pointA
        self.pointB = pointB
        self.length = distance(self.pointA.pos, self.pointB.pos)
        pointA.sticks.append(self)
        pointB.sticks.append(self)
    
    def get_center(self):
        return ((self.pointA.pos[0]+self.pointB.pos[0])/2, (self.pointA.pos[1]+self.pointB.pos[1])/2)
    
    def get_stress(self):
        return distance(self.pointA.pos, self.pointB.pos)-self.length
    
    def get_stress_color(self): # returns an RGB color based on the current stress of the stick
        return (min(max(30+self.get_stress()*(255-30)/MAX_STRESS, 0), 255), min(max(120-self.get_stress()*8, 0), 255), 50)

    def get_points(self): # return connected points as a list
        return [self.pointA, self.pointB]


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

                if p.pos[0] > SCREEN_WIDTH-POINT_RADIUS: # bounce off right
                    excess = p.pos[0]-(SCREEN_WIDTH-POINT_RADIUS)
                    p.prev_pos = (p.pos[0]+0.5*(p.pos[0]-p.prev_pos[0])-excess, p.prev_pos[1])
                    p.pos = (SCREEN_WIDTH-POINT_RADIUS, p.pos[1])

                if p.pos[0] < POINT_RADIUS: # bounce off left
                    excess = p.pos[0]-POINT_RADIUS
                    p.prev_pos = (p.pos[0]+0.5*(p.pos[0]-p.prev_pos[0])-excess, p.prev_pos[1])
                    p.pos = (POINT_RADIUS, p.pos[1])

                if p.pos[1] > SCREEN_HEIGHT-POINT_RADIUS: # bounce off bottom
                    excess = p.pos[1]-(SCREEN_HEIGHT-POINT_RADIUS)
                    p.prev_pos = (p.prev_pos[0], p.pos[1]+0.5*(p.pos[1]-p.prev_pos[1])-excess)
                    p.pos = (p.pos[0], SCREEN_HEIGHT-POINT_RADIUS)

                if p.pos[1] < POINT_RADIUS: # bounce off top
                    excess = p.pos[1]-POINT_RADIUS
                    p.prev_pos = (p.prev_pos[0], p.pos[1]+0.5*(p.pos[1]-p.prev_pos[1])-excess)
                    p.pos = (p.pos[0], POINT_RADIUS)
        
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

    def create_fabric(self, pos, width, height, space_between):
        grid = [[Point((pos[0]+x*space_between, pos[1]+y*space_between), False, False) for x in range(width)] for y in range(height)]
        for row in grid:
            for point in row:
                self.points.append(point)
        for y in range(height):
            for x in range(width-1):
                self.sticks.append(Stick(grid[y][x], grid[y][x+1]))
        for y in range(height-1):
            for x in range(width):
                self.sticks.append(Stick(grid[y][x], grid[y+1][x]))


def distance(pos1, pos2):
    return max(math.hypot(pos1[0]-pos2[0], pos1[1]-pos2[1]), 0.001)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ropes")
    clock = pygame.time.Clock()
    game = Game()

    # game.create_fabric((500, 100), 37, 25, 20)

    paused = False
    use_snap = False
    while True:
        clock.tick(60) # maintain framerate

        mouse_pos = pygame.mouse.get_pos() # get mouse position
        place_pos = mouse_pos
        if use_snap:
            place_pos = (round(mouse_pos[0]/GRID_SIZE)*GRID_SIZE, round(mouse_pos[1]/GRID_SIZE)*GRID_SIZE)
        
        # if there is a point nearby, start drawing at that point; otherwise, create a new point
        nearest_point = None
        dist_nearest_point = SNAP_RADIUS
        for point in game.points:
            dist = distance(mouse_pos, point.pos)
            if dist < dist_nearest_point:
                nearest_point = point
                dist_nearest_point = dist

        drawing = False
        deleting = False

        # process inputs
        for event in pygame.event.get():
            if event.type == QUIT: sys.exit()

            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    paused = not paused
                if event.key == K_g:
                    use_snap = not use_snap

            elif event.type == MOUSEBUTTONDOWN and event.button == 1: # set pointA equal to clicked point, otherwise create new point
                if nearest_point:
                    pointA = nearest_point
                else:
                    pointA = Point(place_pos)
                    game.points.append(pointA)

            elif event.type == MOUSEBUTTONUP and event.button == 1: # set pointB and create sticks between points
                if nearest_point:
                    pointB = nearest_point
                else:
                    pointB = Point(place_pos)
                    game.points.append(pointB)
                
                if pointA != pointB:
                    if not any([pointB in stick.get_points() for stick in pointA.sticks]):
                        game.sticks.append(Stick(pointA, pointB))
                elif not pointA.is_new:
                    pointA.locked = not pointA.locked
                
                pointA.is_new = False
                pointB.is_new = False
        
        if pygame.mouse.get_pressed()[0]: # left mouse is being held, preview stick placement
            drawing = True

        if not drawing and pygame.mouse.get_pressed()[2]: # if right mouse button is being held, remove any object hovered near
            deleting = True
            if nearest_point:
                game.points.remove(nearest_point)
                for stick in nearest_point.sticks:
                    try:
                        game.sticks.remove(stick)
                    except Exception:
                        pass
            for stick in game.sticks:
                if distance(mouse_pos, stick.get_center()) < DELETE_RADIUS+STICK_WIDTH:
                    game.sticks.remove(stick)
        
        for point in game.points:
            if point.pos[1] > SCREEN_WIDTH+SCREEN_HEIGHT: # point is far below screen; delete it
                game.points.remove(point)
                for stick in point.sticks:
                    try:
                        game.sticks.remove(stick)
                    except Exception:
                        pass
            
        
        if not paused: game.update(clock.tick()/1000)

        # Visuals
        screen.fill(bg_color)

        if deleting:
            pygame.draw.circle(screen, deleting_color, mouse_pos, DELETE_RADIUS)

        if drawing:
            pygame.draw.line(screen, point_preview_color, pointA.pos, nearest_point.pos if nearest_point else place_pos, STICK_WIDTH)
        
        pygame.draw.circle(screen, point_preview_color, nearest_point.pos if nearest_point else place_pos, POINT_RADIUS) # mouse cursor thingy

        for stick in game.sticks:
            pygame.draw.line(screen, stick.get_stress_color(), stick.pointA.pos, stick.pointB.pos, STICK_WIDTH)
        for point in game.points:
            pygame.draw.circle(screen, locked_point_color if point.locked else point_color, point.pos, POINT_RADIUS)

        if paused:
            pygame.draw.rect(screen, white, Rect(20, 20, 7, 25))
            pygame.draw.rect(screen, point_color, Rect(33, 20, 7, 25))
        if use_snap:
            pygame.draw.line(screen, white, (14, 69), (44, 69), 4)
            pygame.draw.line(screen, white, (14, 81), (44, 81), 4)
            pygame.draw.line(screen, white, (23, 60), (23, 90), 4)
            pygame.draw.line(screen, white, (35, 60), (35, 90), 4)
        
        pygame.display.flip()

        print(f"FPS: {int(clock.get_fps())}")
        

if __name__ == "__main__":
    main()