import RaicerSocket
import pygame
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, IMG_WIDTH, IMG_HEIGHT, print_debug
from ImageUtils import get_ball_position, get_track

s = RaicerSocket.RaicerSocket()
s.connect()

display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))

track = None

while 1:

    ID, status, lap_id, lap_total, damage, rank, image = s.receive()

    if status in [S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED]:
        display.blit(pygame.surfarray.make_surface(image), (0, 0))
        pygame.display.update()

    if status == S_RUNNING:
        print('Game is running')

        # check keys and send commands to server
        pygame.event.pump()  # needed to get the latest events
        keys = pygame.key.get_pressed()  # sequence of flags for each key
        s.send(keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_LEFT], keys[pygame.K_RIGHT])

        # get the position of the ball
        print_debug('Ball at position', get_ball_position(ID, image))

    elif status == S_COUNTDOWN:
        print('Countdown')

        if track is None:
            track = get_track(image)

    elif status == S_WAIT:
        print('Waiting for start')
    elif status == S_FINISHED:
        print('Finished!')
        break
    elif status == S_CRASHED:
        print('Crashed')
        break
    elif status == S_CANCELED:
        print('Canceled')
        break

s.close()
