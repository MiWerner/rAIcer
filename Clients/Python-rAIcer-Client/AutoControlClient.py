import sys
sys.argv.append("--speed")
sys.argv.append("--cp_ids")
sys.argv.append("1")
sys.argv.append("2")

import RaicerSocket
import pygame
import numpy as np
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, IMG_WIDTH, IMG_HEIGHT, print_debug
from Features import FeatureCalculator
import time

fc = None
s = RaicerSocket.RaicerSocket()
s.connect()
display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))
max_speed = 10
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
            speed_x = inputs[0]
            speed_y = inputs[1]
            # Get the vector to the second next checkpoint
            vector_to_next_checkpoint = [inputs[-2], inputs[-1]];
            # Get the angle of the vector and transform it in a range between 0° and 360°
            angle = np.math.atan2(np.linalg.det([vector_to_next_checkpoint, np.asarray([1, 0])]), np.dot(vector_to_next_checkpoint, np.asarray([1, 0])))
            angle = np.degrees(angle) % 360

            up = (1 < angle < 179) and (speed_y >= -max_speed)
            down = (181 < angle < 359) and (speed_y <= max_speed)
            left = (91 < angle < 269) and (speed_x >= -max_speed)
            right = (angle < 89 or angle > 271) and (speed_x <= max_speed)

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
