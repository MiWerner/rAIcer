import sys
sys.argv.append("--speed")
sys.argv.append("--cp_ids")
sys.argv.append("1")
sys.argv.append("--restore_folder")
sys.argv.append("2018-05-20_23-21-05")

import RaicerSocket
import pygame
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, IMG_WIDTH, IMG_HEIGHT, print_debug
from Utils import PATH_TO_SAVINGS, ARGS
import pickle
import numpy as np
import os

from Features import FeatureCalculator
import time
import neat
fc = None

display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))

genome = pickle.load(open(os.path.join(PATH_TO_SAVINGS, ARGS.restore_folder, "winner.p"), "rb"))
neat_config = neat.Config(neat.DefaultGenome,
                          neat.DefaultReproduction,
                          neat.DefaultSpeciesSet,
                          neat.DefaultStagnation,
                          os.path.join(PATH_TO_SAVINGS, ARGS.restore_folder, "configfile"))

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

            # send keys strokes to server
            socket.send_key_msg(output[0], output[1], output[2], output[3])

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
