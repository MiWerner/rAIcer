import RaicerSocket
import pygame
import numpy as np
import MatrixOps
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
                fc.update(img=image, print_features=False)

        if status == S_RUNNING:
            # Just so the display updates
            pygame.event.get()

            inputs = np.asarray(list(fc.features), dtype=np.int64)
            # Get the vector to the third next checkpoint
            vector_to_next_checkpoint = inputs[16:18]
            # Get the angle of the vector and transform it in a range between 0° and 360°
            angle = np.math.atan2(np.linalg.det([vector_to_next_checkpoint, np.asarray([1, 0])]), np.dot(vector_to_next_checkpoint, np.asarray([1, 0])))
            angle = np.degrees(angle) % 360
            up = 22.5 < angle < 157.5
            down = 202.5 < angle < 337.5
            left = 112.5 < angle < 247.5
            right = angle < 67.5 or angle > 292.5

            s.send_key_msg(up, down, left, right)

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
