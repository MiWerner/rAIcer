import socket
from Utils import TCP_IP, TCP_PORT, IMG_HEIGHT, IMG_WIDTH, print_debug
from ImageUtils import byte_array_to_image
from threading import Thread


class RaicerSocket(object):

    MSGLEN = 6 + IMG_WIDTH*IMG_HEIGHT*3

    is_active = False
    rs_thread = None
    send_msgs = []

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
        :param ip: the IP address of the server
        :param port: the port of the server
        :return:
        """
        self.socket.connect((ip, port))
        self.is_active = True

    def start__threads(self):
        """
        Starts the threads that receive all message from the server and sends messages to the server
        :return:
        """
        self.rs_thread = Thread(target=self.__receive_and_send_thread, args=())
        self.rs_thread.start()

    def __receive_and_send_thread(self):
        """
        Receives and send messages and save the data als long self.is_active is True
        :return:
        """
        while self.is_active:
            # receive message
            b_msg = self.__receive()
            # save data
            self.id = b_msg[0]
            self.status = b_msg[1]
            self.lap_id = b_msg[2]
            self.lap_max = b_msg[3]
            self.damage = b_msg[4]
            self.rank = b_msg[5]
            self.image = byte_array_to_image(b_msg[6:])

            if self.send_msgs:  # if list contains at least one element
                msg = self.send_msgs[0]
                self.send_msgs.remove(msg)
                self.socket.send(msg)

    def __receive(self):
        """
        Reads the full message sent by the server and returns the data as binary
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

    def receive(self):
        """
        Returns the components of the last received message as a tuple.
        :return: tuple with (ID, status, lap-ID, max_lap, damage, rank, image)
        """
        return self.id, self.status, self.lap_id, self.lap_max, self.damage, self.rank, self.image

    def send(self, up, down, left, right):
        """
        Creates and adds a message for movements commands to a queue of messages
        :param up: flag for moving up
        :param down: flag for moving down
        :param left: flag for moving left
        :param right: flag for moving right
        :return:
        """
        msg = [self.id]
        for flag in [up, down, left, right]:
            msg.append(0x01 if flag else 0x00)
        print_debug(msg)
        self.send_msgs.append(bytes(msg))

    def close(self):
        """
        Close the current connection
        :return:
        """

        self.is_active = False
        if self.rs_thread is not None:
            self.rs_thread.join()
            self.rs_thread = None
        self.socket.close()
