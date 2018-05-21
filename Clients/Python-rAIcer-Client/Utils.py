import os
import multiprocessing
import subprocess
import platform

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
#                Feature Parameters                      #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
EN_HV_DIST = True
EN_DIAG_DIST = True
EN_SPEED = True
EN_BALLPOS = True
NUM_CP_FEATURES = 3
IO_NAMES = {
    0: "up",
    1: "down",
    2: "left",
    3: "right",
    -1: "du",
    -2: "dur",
    -3: "dr",
    -4: "ddr",
    -5: "dd",
    -6: "ddl",
    -7: "dl",
    -8: "dul",
    -9: "vx",
    -10: "vy",
    -11: "bpx",
    -12: "bpy",
    -13: "cp1x",
    -14: "cp1y",
    -15: "cp2x",
    -16: "cp2y",
    -17: "cp3x",
    -18: "cp3y",
}

feature_print_string = "ID {}: du={} | dur={} | dr={} | ddr={} | dd={} | ddl={} | dl={} | dul={} | vx={} | vy={} | " \
                       "bp=({}, {}) | cp1=({}, {}) | cp2=({}, {}) | cp3=({}, {})"


def update_feature_parameters(hv_dist=True, diag_dist=True, speed=True, ball_pos=True, num_cp_features=3):
    global EN_HV_DIST, EN_DIAG_DIST, EN_SPEED, EN_BALLPOS, NUM_CP_FEATURES, IO_NAMES, feature_print_string
    EN_HV_DIST = hv_dist
    EN_DIAG_DIST = diag_dist
    EN_SPEED = speed
    EN_BALLPOS = ball_pos
    NUM_CP_FEATURES = num_cp_features

    counter = -1
    IO_NAMES = {
        0: "up",
        1: "down",
        2: "left",
        3: "right",
    }

    feature_print_string = "ID {}: "

    hv_dist = ["du", "dr", "du", "dl"]
    diag_dist = ["dur", "ddr", "ddl", "dul"]
    for i in range(4):
        if EN_HV_DIST:
            IO_NAMES.update({counter: hv_dist[i]})
            feature_print_string += hv_dist[i]+"={} | "
            counter -= 1
        if EN_DIAG_DIST:
            IO_NAMES.update({counter: diag_dist[i]})
            feature_print_string += diag_dist[i] + "={} | "
            counter -= 1

    if EN_SPEED:
        IO_NAMES.update({counter: "vx"})
        feature_print_string += "vx={} | "
        counter -= 1
        IO_NAMES.update({counter: "vy"})
        feature_print_string += "vy={} | "
        counter -= 1

    # TODO add bp and cps to print string

    if EN_BALLPOS:
        IO_NAMES.update({counter: "bpx"})
        counter -= 1
        IO_NAMES.update({counter: "bpy"})
        counter -= 1
        feature_print_string += "bp=({}, {}) | "

    for i in range(1, NUM_CP_FEATURES+1):
        IO_NAMES.update({counter: "cp{}x".format(i)})
        counter -= 1
        IO_NAMES.update({counter: "cp{}y".format(i)})
        counter -= 1
        feature_print_string += "cp" + str(i) + "=({}, {}) | "
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   Debug Messages                      #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
DEBUG = True


def print_debug(msg):
    if DEBUG:
        print(msg)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   path links                          #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
PATH_TO_ROOT = os.path.dirname(os.path.realpath(__file__))
PATH_TO_RES = os.path.join(PATH_TO_ROOT, "res")
PATH_TO_CONFIGS = os.path.join(PATH_TO_RES, "configs")
PATH_TO_SAVINGS = os.path.join(PATH_TO_RES, "NEAT-AI")
PATH_TO_SERVERS = os.path.abspath(os.path.join(os.path.join(PATH_TO_ROOT, os.pardir), os.pardir))
PATH_TO_WINDOWS_CUSTOM_SERVER = os.path.join(PATH_TO_SERVERS, "Custom_Server", "rAIcer.exe")
PATH_TO_LINUX_CUSTOM_SERVER = os.path.join(PATH_TO_SERVERS, "Custom_Server_Linux", "rAIcer.x86_64")
PATH_TO_ORIGINAL_SERVER = os.path.join(PATH_TO_SERVERS, "Server", "rAIcer.exe")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                 Start Server                          #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def _start_server_linux():
    """
    Starts the Linux-version of the rAIcer-server as a new process
    :return: the process of the server
    """
    return multiprocessing.Process(target=subprocess.check_output,
                                   args=([PATH_TO_LINUX_CUSTOM_SERVER]),
                                   kwargs={'stderr': subprocess.STDOUT})


def _start_server_windows():
    """
    Starts the Windows-version of the rAIcer-server as a new process
    :return: the process of the server
    """
    return multiprocessing.Process(target=subprocess.check_output,
                                   args=([PATH_TO_WINDOWS_CUSTOM_SERVER]),
                                   kwargs={'stderr': subprocess.STDOUT})


pf = platform.platform()
if 'Linux' in pf:
    start_server = _start_server_linux
elif 'Windows' in pf:
    start_server = _start_server_windows
else:
    raise ValueError("Unkown Operation-System")


def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path

