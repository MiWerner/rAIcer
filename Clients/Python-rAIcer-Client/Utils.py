import os
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                Server Parameter                       #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
TCP_IP = '127.0.0.1'
TCP_PORT = 5007


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                 Image Parameters                      #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
IMG_WIDTH = 512
IMG_HEIGHT = 288


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   State Values                        #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
S_WAIT = 0
S_COUNTDOWN = 1
S_RUNNING = 2
S_FINISHED = 3
S_CRASHED = 4
S_CANCELED = 5


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   Debug Messages                      #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
DEBUG = True


def print_debug(*args):
    if DEBUG:
        print(args)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   path links                          #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
PATH_TO_ROOT = os.path.dirname(os.path.realpath(__file__))
PATH_TO_RES = os.path.join(PATH_TO_ROOT, "res")
PATH_TO_CONFIGS = os.path.join(PATH_TO_RES, "configs")


def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path
