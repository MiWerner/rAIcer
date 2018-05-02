import RaicerSocket
import pygame
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, IMG_WIDTH, IMG_HEIGHT, print_debug
from ImageUtils import get_ball_position, get_track
from Features import calc_distance_features, draw_features, calc_speed_features
import time
import numpy as np

s = RaicerSocket.RaicerSocket()
s.connect()
display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))

track = None
last_ball_pos = None

while 1:

    ID, status, lap_id, lap_total, damage, rank, image = s.receive()

    if status == S_RUNNING:
        print_debug('Game is running')

        # check keys and send commands to server
        pygame.event.pump()  # needed to get the latest events
        keys = pygame.key.get_pressed()  # sequence of flags for each key
        s.send(keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_LEFT], keys[pygame.K_RIGHT])

        # get the position of the ball
        ball_pos = get_ball_position(ID, image)
        ball_pos = np.asarray(ball_pos, np.int64)
        print_debug('Ball at position', ball_pos)

        du, dd, dl, dr = calc_distance_features(ball_pos, track)
        vx, vy = calc_speed_features(last_ball_pos, ball_pos)
        print_debug("vx: ", vx, ", vy", vy)
        last_ball_pos = ball_pos

        display.blit(pygame.surfarray.make_surface(image), (0, 0))
        draw_features(display, ball_pos, du, dd, dl, dr)
        pygame.display.update()

    elif status == S_COUNTDOWN:
        display.blit(pygame.surfarray.make_surface(image), (0, 0))
        pygame.display.update()
        print_debug('Countdown')
        if track is None:
            track = get_track(image)

        time.sleep(0.1)
    elif status == S_WAIT:
        display.blit(pygame.surfarray.make_surface(image), (0, 0))
        pygame.display.update()
        print_debug('Waiting for start')
        time.sleep(0.1)
    elif status == S_FINISHED:
        display.blit(pygame.surfarray.make_surface(image), (0, 0))
        pygame.display.update()
        print_debug('Finished!')
        break
    elif status == S_CRASHED:
        print_debug('Crashed')
        break
    elif status == S_CANCELED:
        print_debug('Canceled')
        break


s.close()
