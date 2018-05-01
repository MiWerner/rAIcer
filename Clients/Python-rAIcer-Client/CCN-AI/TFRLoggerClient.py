import pygame
import numpy as np
import RaicerSocket
from ImageUtils import get_ball_position
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CRASHED, S_CANCELED, IMG_WIDTH, IMG_HEIGHT, print_debug
# from .TFRLogger import create_tfrecord_writer, close_tfrecord_writer, save_data
#from TFRLogger import create_tfrecord_writer, close_tfrecord_writer, save_data
import os

s = RaicerSocket.RaicerSocket()
s.connect()

display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))

#tfrecord_writer = create_tfrecord_writer(os.path.join(os.getcwd(), "testfile.tfr"))

file = open(os.path.join(os.getcwd(), "testfile.txt"), 'w')
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

        keys = np.array([keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_LEFT], keys[pygame.K_RIGHT]], dtype=np.uint8)

        np.savetxt(os.path.join(os.getcwd(), "testfile.txt"),
                   np.reshape(np.asarray(image, np.uint8), (1, -1)),
                   delimiter="%u%")
        np.savetxt(os.path.join(os.getcwd(), "testfile.txt"), keys, delimiter="%u")



        #file.write(str({'img': image, 'keys': keys}))  # dict == eval(str(dict))
        #np.save(file, image)
        #np.save(file, keys)
        #np.savetxt(os.path.join(os.getcwd(), "testfile.txt"), image.astype(int), fmt='%i')
        #np.savetxt(os.path.join(os.getcwd(), "testfile.txt"), keys.astype(int), fmt='%i')
#        save_data(tfrecord_writer=tfrecord_writer,
#                  b_image=s.b_image,
#                  keys=keys)

        # get the position of the ball
        # print_debug('Ball at position', get_ball_position(ID, image))

    elif status == S_COUNTDOWN:
        print('Countdown')
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

#close_tfrecord_writer(tfrecord_writer)
file.close()
s.close()
