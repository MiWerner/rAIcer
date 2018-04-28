import socket
from Utils import TCP_IP, TCP_PORT, IMG_HEIGHT, IMG_WIDTH, print_debug
import numpy as np


class RaicerSocket(object):

    MSGLEN = 6 + IMG_WIDTH*IMG_HEIGHT*3

    id = -1

    status = -1

    lap_id = -1

    lap_max = -1

    damage = -1

    rank = -1

    image = -1

    def __init__(self):
        """Initialize the socket"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, ip=TCP_IP, port=TCP_PORT):
        """
        Connects the socket to the address defined by ip and port
        :param ip: the IP-Adress of the
        :param port: the Port-ID
        :return:
        """
        self.socket.connect((ip, port))

    @staticmethod
    def convert_image(b_img):
        """
        Converts the binary image b_img into a normal image
        :param b_img: the binary image
        :return: converted image
        """
        img = np.fromstring(b_img, dtype=np.uint8)
        img = img.reshape(IMG_HEIGHT, IMG_WIDTH, 3)
        img = np.transpose(img, (1, 0, 2))
        img = np.flip(img, 1) # Invert x axis
        return img

    def __recieve(self):
        """
        Reads a the full message send by the server and returns the data as binary
        :return: binary server message
        """
        chunks = []
        bytes_recd = 0
        while bytes_recd < self.MSGLEN:
            chunk = self.socket.recv(min(self.MSGLEN - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def recieve(self):
        """
        Receives a message from the server, saves the data and return components of the message as a tuple.
        :return: tuple with (ID, status, lap-ID, max_lap, damage, rank, image)
        """
        data = self.__recieve()
        print_debug("Length", len(data))
        self.id = data[0]
        self.status = data[1]
        self.lap_id = data[2]
        self.lap_max = data[3]
        self.damage = data[4]
        self.rank = data[5]
        self.image = self.convert_image(data[6:])

        return self.id, self.status, self.lap_id, self.lap_max, self.damage, self.rank, self.image

    def send(self, up, down, left, right):
        """
        Sends a message to the server containing the commands for moving
        :param up: flag for moving up-war
        :param down: flag for moving down
        :param left: flag for moving to the left
        :param right: flag for moving to the right
        :return:
        """
        msg = [self.id]
        for flag in [up, down, left, right]:
            msg.append(0x01 if flag else 0x00)
        print_debug(msg)
        self.socket.send(bytes(msg))

    def close(self):
        """
        Close the current connection
        :return:
        """
        self.socket.close()