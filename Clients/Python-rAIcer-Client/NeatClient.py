import sys
sys.argv.append("--direc_dist")
sys.argv.append("--speed")
sys.argv.append("--cp_ids")
sys.argv.append("2")
sys.argv.append("--output_mode_2")
sys.argv.append("--restore_folder")
sys.argv.append("tmp")

import RaicerSocket
import pygame
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, IMG_WIDTH, IMG_HEIGHT, print_debug
from Utils import PATH_TO_EXPERIMENTS, ARGS
import pickle
import numpy as np
import os

from Features import FeatureCalculator
import time
import neat
fc = None

display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))

genome = pickle.load(open(os.path.join(PATH_TO_EXPERIMENTS, ARGS.restore_folder, "winner_short.p"), "rb"))
neat_config = neat.Config(neat.DefaultGenome,
                          neat.DefaultReproduction,
                          neat.DefaultSpeciesSet,
                          neat.DefaultStagnation,
                          os.path.join(PATH_TO_EXPERIMENTS, ARGS.restore_folder, "configfile"))

net = neat.nn.FeedForwardNetwork.create(genome=genome, config=neat_config)

socket = RaicerSocket.RaicerSocket()
socket.connect()

status = -1
try:
    while 1:

        if socket.new_message:
            ID, status, lap_id, lap_total, damage, rank, image = socket.receive()
            if fc is not None:
                fc.update(img=image, print_features=False)

        if status == S_RUNNING:
            # check keys and send commands to server
            inputs = np.asarray(list(fc.features), dtype=np.int64)

            # calculate key strokes
            output = np.asarray(list(map(lambda x: x + .5, net.activate(inputs=inputs))),
                                dtype=np.int8)

            if ARGS.output_mode_2:
                keys = np.zeros(4)
                # vertical control
                if output[0] <= .25:  # down
                    keys[1] = 1
                elif output[0] >= .75:  # up
                    keys[0] = 1
                # horizontal control
                if output[1] <= .25:  # right
                    keys[3] = 1
                elif output[1] >= .75:  # left
                    keys[2] = 1
            else:
                keys = output

            # if not power_up_used:
            #    power_up_used = True
            #    if keys[0] == 0 and keys[1] == 0 and keys[2] == 0 and keys[3] == 0:
            #        keys[3] = 1

            # send keys strokes to server
            socket.send_key_msg(keys[0], keys[1], keys[2], keys[3])

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
    socket.close()
