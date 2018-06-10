import os
import multiprocessing
import subprocess
import platform
import argparse

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                       Parser                          #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
parser = argparse.ArgumentParser()

parser.add_argument("--hv_dists", action="store_true", default=False, help="Enables hv distances features")
parser.add_argument("--diag_dists", action="store_true", default=False, help="Enables diagonal distances features")
parser.add_argument("--speed", action="store_true", default=False, help="Enables speed features")
parser.add_argument("--ballpos", action="store_true", default=False, help="Enables ballpos features")
parser.add_argument("--cp_ids", nargs='*', type=int, default=[1, 2, 3], help="Sets the IDs of requested Checkpoints in feature vector as a list")
parser.add_argument("--config", type=str, default=None, help="filename of the configfile in config folder")
parser.add_argument("--restore", action="store_true", default=None,
                    help="If set the population is restored from the file defined by restore_folder and checkpoint_id")
parser.add_argument("--restore_folder", type=str, default=None, help="folder name of the run to restore")
parser.add_argument("--checkpoint_id", type=int, default=None, help="id of the checkpoint used to restore run")
parser.add_argument("--num_gen", type=int, default=100, help="The number of generations to run")

ARGS = parser.parse_args()

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
#                   IO_NAMES                            #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

IO_NAMES = {
    0: "up",
    1: "down",
    2: "left",
    3: "right",
}
counter = -1

hv_dist = ["du", "dr", "du", "dl"]
diag_dist = ["dur", "ddr", "ddl", "dul"]
for i in range(4):
    if ARGS.hv_dists:
        IO_NAMES.update({counter: hv_dist[i]})
        counter -= 1
    if ARGS.diag_dists:
        IO_NAMES.update({counter: diag_dist[i]})
        counter -= 1

if ARGS.speed:
    IO_NAMES.update({counter: "vx"})
    counter -= 1
    IO_NAMES.update({counter: "vy"})
    counter -= 1

if ARGS.ballpos:
    IO_NAMES.update({counter: "bpx"})
    counter -= 1
    IO_NAMES.update({counter: "bpy"})
    counter -= 1

for i in ARGS.cp_ids:
    IO_NAMES.update({counter: "cp{}x".format(i)})
    counter -= 1
    IO_NAMES.update({counter: "cp{}y".format(i)})
    counter -= 1

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   feature print string                #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
feature_print_string = "ID {}: "

hv_dist = ["du", "dr", "du", "dl"]
diag_dist = ["dur", "ddr", "ddl", "dul"]
for i in range(4):
    if ARGS.hv_dists:
        feature_print_string += hv_dist[i]+"={} | "
    if ARGS.diag_dists:
        feature_print_string += diag_dist[i] + "={} | "

if ARGS.speed:
    feature_print_string += "vx={} | vy={} | "

if ARGS.ballpos:
    feature_print_string += "bp=({}, {}) | "

for i in ARGS.cp_ids:
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
