import sys
sys.argv.append("--speed")
sys.argv.append("--hv_dist")
sys.argv.append("--diag_dist")
sys.argv.append("--ballpos")
sys.argv.append("--cp_ids")
sys.argv.append("1")
sys.argv.append("2")
sys.argv.append("4")
sys.argv.append("7")

import RaicerSocket
import pygame
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, IMG_WIDTH, IMG_HEIGHT, print_debug
from Features import FeatureCalculator
import time

fc = None
s = RaicerSocket.RaicerSocket()
s.connect()
display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))

status = -1
try:
    while 1:

        if s.new_message:
            ID, status, lap_id, lap_total, damage, rank, image = s.receive()
            if fc is not None:
                fc.update(img=image, print_features=True)

        if status == S_RUNNING:
            # check keys and send commands to server
            pygame.event.pump()  # needed to get the latest events
            keys = pygame.key.get_pressed()  # sequence of flags for each key
            s.send_key_msg(keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_LEFT], keys[pygame.K_RIGHT])

            display.blit(pygame.surfarray.make_surface(image), (0, 0))
            fc.draw_features(display)
            pygame.display.update()

        elif status == S_COUNTDOWN:
            display.blit(pygame.surfarray.make_surface(image), (0, 0))
            pygame.display.update()
            if fc is None:
                fc = FeatureCalculator(img=image, client_id=ID)

            time.sleep(0.1)
        elif status == S_WAIT:
            display.blit(pygame.surfarray.make_surface(image), (0, 0))
            pygame.display.update()

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

        time.sleep(.1)
finally:
    s.close()
