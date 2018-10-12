import RaicerSocket
import neat
from Features import FeatureCalculator
import numpy as np
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CANCELED, S_CRASHED
import time


class TournamentClient(object):
    time_out_zero_speed_counter = 100  # due time.sleep(.1) the run is over after 20 sec of zero speed
    zero_speed_counter = 0

    start_timestamp = None

    race_time = None

    damage = None

    thread = None

    fc = None

    track = None

    track_line = None

    def __init__(self, cp_ids, output_mode_2):
        self.socket = RaicerSocket.RaicerSocket()
        self.cp_ids = cp_ids
        self.output_mode_2 = output_mode_2

    def __connect_to_server(self):
        """
        Tries to connect to the server for 100s.
        :return: True if connection was successful, else False
        """
        t = time.time() + 100
        while time.time() <= t:
            try:
                self.socket.connect()
                return True
            except ConnectionRefusedError:
                time.sleep(.5)
        return False

    def run(self, genome_id, net, out_q, max_id, track_id):
        """
        Starts the connection to the server. Then runs the genome of this evaluator as a Client.
        When the game is over the connection is closed and the fitness-value saved in the given output-queue
        :param genome_id: the id of the corresponding genome in the current generation
        :param genome: the corresponding genome
        :param config: the current configuration
        :param out_q: Queue where the fitness-value of the genome is stored
        :param max_id: the largest id in the current race
        :param track_id: the id of the track for the current race. The numbering starts with 1
        :param num_laps: the number of laps in the current race
        :return:
        """
        if not self.__connect_to_server():
            return

        # receive client_id to check if all current clients are connected
        client_id = None
        while client_id in [None, -1]:
            client_id, *_ = self.socket.receive()
            time.sleep(.1)
        if client_id == max_id:
            # if current id is the largest possible, this client is the last one and should start the game
            self.socket.send_setting_msg(track_id=track_id, num_laps=5)

        # start client behavior
        self.__client_logic(net=net)

        # transfer fitness-value to main process
        # TODO send time and damage
        if self.damage is None:
            self.damage = 255
        if self.race_time is None:
            self.race_time = time.time() - self.start_timestamp
        out_q.put({genome_id: (self.race_time, self.damage)})

    def __client_logic(self, net):
        """
        The Client-logic according to the given network.
        Server messages are received. Based on the image the features are calculated.
        The features are used as network input.
        The output of the network is send to the server.
        Also statistics for the fitness-value are stored
        :param net: the network used to calculate the key-strokes
        :return:
        """
        status = -1
        power_up_used = False
        while True:

            if not self.socket.is_active:
                return

            if self.socket.new_message:
                # receive new message
                client_id, status, lap_id, lap_total, damage, rank, image = self.socket.receive()
                if self.fc is not None:
                    self.fc.update(img=image, print_features=False)

                if damage is not None:
                    self.damage = damage

            if status == S_WAIT:
                # wait for game to start
                pass

            elif status == S_COUNTDOWN:
                # extract track during countdown
                if self.fc is None:
                    self.fc = FeatureCalculator(client_id=client_id, img=image)

            elif status == S_RUNNING:
                if self.start_timestamp is None:
                    # set timestamp when race stated for fitness calculation
                    self.start_timestamp = time.time()

                inputs = np.asarray(list(self.fc.feature_m(speed=True, cp_ids=self.cp_ids, direc_dist=True)), dtype=np.int64)

                # calculate key strokes
                output = net.activate(inputs=inputs)

                if self.output_mode_2:
                    keys = np.zeros(4)
                    # vertical control
                    if output[0] <= .25: # down
                        keys[0] = 0
                        keys[1] = 1
                    elif output[0] >= .75: # up
                        keys[0] = 1
                        keys[1] = 0
                    # horizontal control
                    if output[1] <= .25: # right
                        keys[2] = 0
                        keys[3] = 1
                    elif output[1] >= .75: # left
                        keys[2] = 1
                        keys[3] = 0

                else:
                    keys = np.asarray(list(map(lambda x: x + .5, output)),
                                      dtype=np.int8)

                if not power_up_used:
                   power_up_used = True
                   if keys[0] == 0 and keys[1] == 0 and keys[2] == 0 and keys[3] == 0:
                       keys[3] = 1

                # send keys strokes to server
                self.socket.send_key_msg(keys[0], keys[1], keys[2], keys[3])

                speed = self.fc.speed_features
                if speed[0] == 0 and speed[1] == 0:
                    self.zero_speed_counter += 1

                if self.zero_speed_counter >= self.time_out_zero_speed_counter:
                    return

            elif status == S_FINISHED:
                # save time of racing
                self.race_time = time.time() - self.start_timestamp
                return

            elif status == S_CRASHED:
                # client broke
                return

            elif status == S_CANCELED:
                return

            time.sleep(.1)
