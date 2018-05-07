import socket
from Utils import TCP_IP, TCP_PORT, IMG_HEIGHT, IMG_WIDTH, S_WAIT
from ImageUtils import byte_array_to_image
from threading import Thread


class RaicerSocket(object):

    MSGLEN = 6 + IMG_WIDTH*IMG_HEIGHT*3

    is_active = False
    thread = None

    id = -1
    status = -1
    lap_id = -1
    lap_max = -1
    damage = -1
    rank = -1
    image = -1

    new_message = False
    __keys_msg = None
    __setting_msg = None
    __kill_msg = None

    def __init__(self):
        """Initialize the socket"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, ip=TCP_IP, port=TCP_PORT):
        """
        Connects the socket to the address defined by ip and port and starts the communication thread
        :param ip: the IP address of the server
        :param port: the port of the server
        :return:
        """
        self.socket.connect((ip, port))
        self.is_active = True

        self.thread = Thread(target=self.__receive_and_send_thread, args=())
        self.thread.daemon = True
        self.thread.start()

    def __receive_and_send_thread(self):
        """
        Receives and sends messages and saves the data as long as self.is_active is True.
        After receiving a message the flag new_message will be set
        :return:
        """
        while self.is_active:
            # send the latest message if it exists
            if self.__keys_msg is not None:
                self.socket.send(self.__keys_msg)
                self.__keys_msg = None
            if self.__setting_msg is not None:
                self.socket.send(self.__setting_msg)
                self.__setting_msg = None
            if self.__kill_msg is not None:
                self.socket.send(self.__kill_msg)
                self.__kill_msg = None

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
            self.new_message = True

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
        Resets the flag new_message because the newest message is delivered now.
        :return: tuple with (ID, status, lap-ID, max_lap, damage, rank, image)
        """
        self.new_message = False
        return self.id, self.status, self.lap_id, self.lap_max, self.damage, self.rank, self.image

    def send_key_msg(self, up, down, left, right):
        """
        Creates and sets the message for movements commands
        :param up: flag for moving up
        :param down: flag for moving down
        :param left: flag for moving left
        :param right: flag for moving right
        :return:
        """
        msg = [self.id]
        for flag in [up, down, left, right]:
            msg.append(0x01 if flag else 0x00)
        self.__keys_msg = bytes(msg)

    def send_kill_msg(self):
        """
        Queues a message for the server with a ID of 255. This results into shutdown the server
        :return:
        """
        self.__kill_msg = bytes([11, 0, 0, 0, 0])
        self.socket.send(self.__kill_msg)

    def send_setting_msg(self, track_id=1, num_laps=3, start_countdown=True):
        """
        Queues a message for the server as long self.status is S_WAIT.
        This message could be used to choose a map, set the maximum number of laps and to start the countdown
        :param track_id: the id of a track (Numbering starts with 1)
        :param num_laps: the maximum number of laps in this race
        :param start_countdown: int or boolean. If not 0 the countdown starts
        :return:
        """
        if self.status == S_WAIT:
            self.__setting_msg = bytes([self.id, track_id, num_laps, 0, int(start_countdown)])

    def close(self):
        """
        Close the current connection
        :return:
        """
        if self.__kill_msg is not None:
            self.socket.send(self.__kill_msg)
        self.is_active = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None
        self.socket.close()
