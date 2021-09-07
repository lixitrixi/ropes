# Imports
import pygame
from pygame.locals import *
import sys, math
from objects import Point, Stick, Game


# Vars
ACC_X = 0 # global x acceleration
ACC_Y = 500 # global y acceleration

USE_STRESS = True
MAX_STRESS = 4.5

SNAP_SIZE = 25 # size (in pixels) of the snapping grid
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


def distance(pos1, pos2):
    return math.hypot(pos1[0]-pos2[0], pos1[1]-pos2[1])

def main():
    pygame.init()
    screen = pygame.display.set_mode((1792,1075))
    pygame.display.set_caption("Ropes")
    clock = pygame.time.Clock()
    game = Game()

    paused = False
    use_snap = False
    while True:
        clock.tick(60) # maintain framerate

        mouse_pos = pygame.mouse.get_pos() # get mouse position
        place_pos = mouse_pos
        if use_snap:
            place_pos = (round(mouse_pos[0]/SNAP_SIZE)*SNAP_SIZE, round(mouse_pos[1]/SNAP_SIZE)*SNAP_SIZE)
        
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
                    pointA = Point(place_pos, False)
                    game.points.append(pointA)

            elif event.type == MOUSEBUTTONUP and event.button == 1: # set pointB and create sticks between points
                if nearest_point:
                    pointB = nearest_point
                else:
                    pointB = Point(place_pos, False)
                    game.points.append(pointB)
                
                if pointA != pointB:
                    game.sticks.append(Stick(pointA, pointB, distance(pointA.pos, pointB.pos)))
                elif not pointA.is_new:
                    pointA.locked = not pointA.locked
                
                pointA.is_new = False
                pointB.is_new = False
        
        if pygame.mouse.get_pressed()[0]: # left mouse is being held, preview stick placement
            drawing = True

        if pygame.mouse.get_pressed()[2]: # if right mouse button is being held, remove any object hovered near
            deleting = True
            if nearest_point:
                game.points.remove(nearest_point)
                for stick in nearest_point.sticks:
                    try:
                        game.sticks.remove(stick)
                    except Exception:
                        pass
            for stick in game.sticks:
                if distance(mouse_pos, stick.get_center()) < DELETE_RADIUS + STICK_WIDTH:
                    game.sticks.remove(stick)
        
        for point in game.points:
            if point.pos[1] > 1800: # point is far below screen; delete it
                game.points.remove(point)
                for stick in point.sticks:
                    try:
                        game.sticks.remove(stick)
                    except Exception:
                        pass
            
        
        if not paused: game.update(clock.tick()/1000)

        # Visuals
        screen.fill(bg_color)
        
        if drawing:
            pygame.draw.line(screen, point_preview_color, pointA.pos, place_pos, STICK_WIDTH)
        
        if deleting:
            pygame.draw.circle(screen, deleting_color, mouse_pos, DELETE_RADIUS)

        if not deleting: 
            pygame.draw.circle(screen, point_preview_color, place_pos, POINT_RADIUS) # point placing overlay

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
        

if __name__ == "__main__":
    main()