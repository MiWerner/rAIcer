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
