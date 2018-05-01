from TFRLogger import input_pipeline
import tensorflow as tf
import os
import pygame
from Utils import  IMG_WIDTH, IMG_HEIGHT

display = pygame.display.set_mode((IMG_WIDTH, IMG_HEIGHT))
display.fill((255, 64, 64))

#graph = tf.Graph()

#with graph.as_default():
#    image_batch, keys_batch = input_pipeline(filenames=[os.path.join(os.getcwd(), "testfile.tfr")],
#                                             num_read_threads=1,
#                                             num_epochs=1,
#                                             batch_size=1)

#sess = tf.Session(graph=graph)
#sess.run(tf.local_variables_initializer())
#sess.run(tf.global_variables_initializer())
#coord = tf.train.Coordinator()
#threads = tf.train.start_queue_runners(sess=sess, coord=coord)

#while not coord.should_stop():

#    image, keys = sess.run([image_batch, keys_batch])

#    print(keys)
#    display.blit(pygame.surfarray.make_surface(image), (0, 0))
#    pygame.display.update()
#else:
#    coord.request_stop()
#coord.join(threads)
#sess.close()

import numpy as np

record_iterator = tf.python_io.tf_record_iterator(path=os.path.join(os.getcwd(), "testfile.tfr"))

for string_record in record_iterator:
    example = tf.train.Example()
    example.ParseFromString(string_record)

    image_string = example.features.feature['image'].bytes_list.value[0]

    keys = example.features.feature['keys'].int64_list.value[0]

    image = np.fromstring(image_string, dtype=np.uint8)
    image = image.reshape((IMG_HEIGHT, IMG_WIDTH, 3))
    print(np.size(image))
    # keys = np.fromstring(keys, dtype=np.uint8)
    print(keys)
    display.blit(pygame.surfarray.make_surface(image), (0, 0))
    pygame.display.update()