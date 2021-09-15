# Imports
import pygame
from pygame.locals import *
import sys, math
import random
import copy


# Vars
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500

ACC_X = 0 # global x acceleration
ACC_Y = 500 # global y acceleration

BALLOON_ACC_X = 0
BALLOON_ACC_Y = -250

USE_STRESS = False
MAX_STRESS = 4.5

GRID_SIZE = 25 # size (in pixels) of the snapping grid
SNAP_RADIUS = 20 # within this distance, a stick will snap to the nearest node while being created
DELETE_RADIUS = 10

NODE_RADIUS = 7
BALLOON_RADIUS = 15
STICK_WIDTH = 7

white = (255, 255, 255)
bg_color = (65, 65, 130)
node_preview_color = (85, 85, 160)
node_color = (255, 255, 255)
balloon_color = (161, 27, 191)
locked_node_color = (255, 75, 75)
deleting_color = (255, 105, 105)


# Classes
class Node(): # parent node class
    def __init__(self, pos, locked=False, is_new=True): # pos = (x, y); locked = bool
        self.pos = pos
        self.prev_pos = pos
        self.locked = locked
        self.is_new = is_new # this node is currently being created; don't apply physics to it
        self.sticks = []

    def update(self, d_time):

        pos_before_update = self.pos
        self.pos = (2*self.pos[0]-self.prev_pos[0], 2*self.pos[1]-self.prev_pos[1])
        self.pos = (self.pos[0]+ACC_X*(d_time**2), self.pos[1]+ACC_Y*(d_time**2))
        self.prev_pos = pos_before_update

        if self.pos[0] > SCREEN_WIDTH-NODE_RADIUS: # bounce off right
            excess = self.pos[0]-(SCREEN_WIDTH-NODE_RADIUS)
            self.prev_pos = (self.pos[0]+0.5*(self.pos[0]-self.prev_pos[0])-excess, self.prev_pos[1])
            self.pos = (SCREEN_WIDTH-NODE_RADIUS, self.pos[1])

        if self.pos[0] < NODE_RADIUS: # bounce off left
            excess = self.pos[0]-NODE_RADIUS
            self.prev_pos = (self.pos[0]+0.5*(self.pos[0]-self.prev_pos[0])-excess, self.prev_pos[1])
            self.pos = (NODE_RADIUS, self.pos[1])

        if self.pos[1] > SCREEN_HEIGHT-NODE_RADIUS: # bounce off bottom
            excess = self.pos[1]-(SCREEN_HEIGHT-NODE_RADIUS)
            self.prev_pos = (self.prev_pos[0], self.pos[1]+0.5*(self.pos[1]-self.prev_pos[1])-excess)
            self.pos = (self.pos[0], SCREEN_HEIGHT-NODE_RADIUS)

        if self.pos[1] < NODE_RADIUS: # bounce off top
            excess = self.pos[1]-NODE_RADIUS
            self.prev_pos = (self.prev_pos[0], self.pos[1]+0.5*(self.pos[1]-self.prev_pos[1])-excess)
            self.pos = (self.pos[0], NODE_RADIUS)

class Balloon(Node):
    def __init__(self, pos):
        super().__init__(pos)
        self.is_new = False

    def update(self, d_time):

        pos_before_update = self.pos
        self.pos = (2*self.pos[0]-self.prev_pos[0], 2*self.pos[1]-self.prev_pos[1])
        self.pos = (self.pos[0]+BALLOON_ACC_X*(d_time**2), self.pos[1]+BALLOON_ACC_Y*(d_time**2))
        self.prev_pos = pos_before_update

        if self.pos[0] > SCREEN_WIDTH-BALLOON_RADIUS: # bounce off right
            excess = self.pos[0]-(SCREEN_WIDTH-BALLOON_RADIUS)
            self.prev_pos = (self.pos[0]+0.5*(self.pos[0]-self.prev_pos[0])-excess, self.prev_pos[1])
            self.pos = (SCREEN_WIDTH-BALLOON_RADIUS, self.pos[1])

        if self.pos[0] < BALLOON_RADIUS: # bounce off left
            excess = self.pos[0]-BALLOON_RADIUS
            self.prev_pos = (self.pos[0]+0.5*(self.pos[0]-self.prev_pos[0])-excess, self.prev_pos[1])
            self.pos = (BALLOON_RADIUS, self.pos[1])

        if self.pos[1] > SCREEN_HEIGHT-BALLOON_RADIUS: # bounce off bottom
            excess = self.pos[1]-(SCREEN_HEIGHT-BALLOON_RADIUS)
            self.prev_pos = (self.prev_pos[0], self.pos[1]+0.5*(self.pos[1]-self.prev_pos[1])-excess)
            self.pos = (self.pos[0], SCREEN_HEIGHT-BALLOON_RADIUS)

        if self.pos[1] < BALLOON_RADIUS: # bounce off top
            excess = self.pos[1]-BALLOON_RADIUS
            self.prev_pos = (self.prev_pos[0], self.pos[1]+0.5*(self.pos[1]-self.prev_pos[1])-excess)
            self.pos = (self.pos[0], BALLOON_RADIUS)

class Stick():
    def __init__(self, nodeA, nodeB):
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.length = distance(self.nodeA.pos, self.nodeB.pos)
        nodeA.sticks.append(self)
        nodeB.sticks.append(self)
    
    def get_center(self):
        return ((self.nodeA.pos[0]+self.nodeB.pos[0])/2, (self.nodeA.pos[1]+self.nodeB.pos[1])/2)
    
    def get_stress(self):
        return distance(self.nodeA.pos, self.nodeB.pos)-self.length
    
    def get_stress_color(self): # returns an RGB color based on the current stress of the stick
        return (min(max(30+self.get_stress()*(255-30)/MAX_STRESS, 0), 255), min(max(120-self.get_stress()*8, 0), 255), 50)

    def get_nodes(self): # return connected nodes as a list
        return [self.nodeA, self.nodeB]


class Game():
    def __init__(self, nodes=[], sticks=[]):
        self.nodes = nodes
        self.sticks = sticks

    def update(self, d_time): # d_time = time since last frame (IN SECONDS)
        d_time = max(d_time, 0.01)
        for node in self.nodes:
            if not node.locked and not node.is_new:
                node.update(d_time)

        for stick in self.sticks:
            if USE_STRESS and stick.get_stress() > MAX_STRESS:
                self.sticks.remove(stick)
            stick_center = stick.get_center()
            dist = distance(stick.nodeA.pos, stick.nodeB.pos)
            stick_dir = ((stick.nodeA.pos[0]-stick.nodeB.pos[0])/dist, (stick.nodeA.pos[1]-stick.nodeB.pos[1])/dist)
            if not stick.nodeA.locked:
                stick.nodeA.pos = (stick_center[0]+stick_dir[0]*stick.length/2, stick_center[1]+stick_dir[1]*stick.length/2)
            if not stick.nodeB.locked:
                stick.nodeB.pos = (stick_center[0]-stick_dir[0]*stick.length/2, stick_center[1]-stick_dir[1]*stick.length/2)

    def create_fabric(self, pos, width, height, space_between):
        grid = [[Node((pos[0]+x*space_between, pos[1]+y*space_between), False, False) for x in range(width)] for y in range(height)]
        for row in grid:
            for node in row:
                self.nodes.append(node)
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

    # game.create_fabric((100, 100), 17, 15, 20)

    paused = True
    use_snap = False
    while True:
        clock.tick(60) # maintain framerate

        mouse_pos = pygame.mouse.get_pos() # get mouse position
        place_pos = mouse_pos
        if use_snap:
            place_pos = (round(mouse_pos[0]/GRID_SIZE)*GRID_SIZE, round(mouse_pos[1]/GRID_SIZE)*GRID_SIZE)
        
        # if there is a node nearby, start drawing at that node; otherwise, create a new node
        nearest_node = None
        dist_nearest_node = SNAP_RADIUS
        for node in game.nodes:
            dist = distance(mouse_pos, node.pos)
            if dist < dist_nearest_node:
                nearest_node = node
                dist_nearest_node = dist

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
                if event.key == K_b:
                    balloon = Balloon(place_pos)
                    game.nodes.append(balloon)

            elif event.type == MOUSEBUTTONDOWN and event.button == 1: # set nodeA equal to clicked node, otherwise create new node
                if nearest_node:
                    nodeA = nearest_node
                else:
                    nodeA = Node(place_pos)
                    game.nodes.append(nodeA)

            elif event.type == MOUSEBUTTONUP and event.button == 1: # set nodeB and create sticks between nodes
                if nearest_node:
                    nodeB = nearest_node
                else:
                    nodeB = Node(place_pos)
                    game.nodes.append(nodeB)
                
                if nodeA != nodeB:
                    if not any([nodeB in stick.get_nodes() for stick in nodeA.sticks]):
                        game.sticks.append(Stick(nodeA, nodeB))
                elif not nodeA.is_new and not isinstance(nodeA, Balloon):
                    nodeA.locked = not nodeA.locked
                
                nodeA.is_new = False
                nodeB.is_new = False
        
        if pygame.mouse.get_pressed()[0]: # left mouse is being held, preview stick placement
            drawing = True

        if not drawing and pygame.mouse.get_pressed()[2]: # if right mouse button is being held, remove any object hovered near
            deleting = True
            if nearest_node:
                game.nodes.remove(nearest_node)
                for stick in nearest_node.sticks:
                    try:
                        game.sticks.remove(stick)
                    except Exception:
                        pass
            for stick in game.sticks:
                if distance(mouse_pos, stick.get_center()) < DELETE_RADIUS+STICK_WIDTH:
                    game.sticks.remove(stick)
        
        for node in game.nodes:
            if node.pos[1] > SCREEN_WIDTH+SCREEN_HEIGHT: # node is far below screen; delete it
                game.nodes.remove(node)
                for stick in node.sticks:
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
            pygame.draw.line(screen, node_preview_color, nodeA.pos, nearest_node.pos if nearest_node else place_pos, STICK_WIDTH)
        
        pygame.draw.circle(screen, node_preview_color, nearest_node.pos if nearest_node else place_pos, NODE_RADIUS) # mouse cursor thingy

        for stick in game.sticks:
            pygame.draw.line(screen, stick.get_stress_color(), stick.nodeA.pos, stick.nodeB.pos, STICK_WIDTH)
        for node in game.nodes:
            pygame.draw.circle(screen, balloon_color if isinstance(node, Balloon) else (locked_node_color if node.locked else node_color), node.pos, BALLOON_RADIUS if isinstance(node, Balloon) else NODE_RADIUS)

        if paused:
            pygame.draw.rect(screen, white, Rect(20, 20, 7, 25))
            pygame.draw.rect(screen, node_color, Rect(33, 20, 7, 25))
        if use_snap:
            pygame.draw.line(screen, white, (14, 69), (44, 69), 4)
            pygame.draw.line(screen, white, (14, 81), (44, 81), 4)
            pygame.draw.line(screen, white, (23, 60), (23, 90), 4)
            pygame.draw.line(screen, white, (35, 60), (35, 90), 4)
        
        pygame.display.flip()

        print(f"FPS: {int(clock.get_fps())}")
        

if __name__ == "__main__":
    main()