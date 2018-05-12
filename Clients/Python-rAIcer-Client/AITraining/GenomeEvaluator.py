import RaicerSocket
import neat
from ImageUtils import get_ball_position, get_track
from Features import FeatureCalculator
import numpy as np
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CANCELED, S_CRASHED
import time


class GenomeEvaluator(object):

    time_out = 10  # 4*60  # s  (maximum time for one run)

    start_timestamp = None

    race_time = None

    damage = None

    thread = None

    fc = None

    track = None

    track_line = None

    def __init__(self):
        self.socket = RaicerSocket.RaicerSocket()

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

    def run(self, genome_id, genome, config, out_q, max_id, track_id, num_laps=3):
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

        net = neat.nn.FeedForwardNetwork.create(genome=genome, config=config)  # TODO evt also RNN

        # receive client_id to check if all current clients are connected
        client_id = None
        while client_id in [None, -1]:
            client_id, *_ = self.socket.receive()
            time.sleep(.1)
        if client_id == max_id:
            # if current id is the largest possible, this client is the last one and should start the game
            self.socket.send_setting_msg(track_id=track_id, num_laps=num_laps)

        # start client behavior
        self.__client_logic(net=net)

        # transfer fitness-value to main process
        out_q.put({genome_id: self.calc_fitness_value()})

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
        while True:
            if self.socket.new_message:
                # receive new message
                client_id, status, lap_id, lap_total, damage, rank, image = self.socket.receive()
                if self.fc is not None:
                    self.fc.update(img=image, print_features=True)

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

                # TODO include idle-line features
                inputs = np.asarray(list(self.fc.features), dtype=np.int64)

                # calculate key strokes
                output = np.asarray(list(map(lambda x: x + .5, net.activate(inputs=inputs))),
                                    dtype=np.int8)

                # send keys strokes to server
                self.socket.send_key_msg(output[0], output[1], output[2], output[3])

                # TODO evt. save more statistics for fitness-value

            elif status == S_FINISHED:
                # save time of racing
                self.race_time = time.time() - self.start_timestamp
                return

            elif status == S_CRASHED:
                # client broke
                # TODO think about different  punishment
                self.race_time = self.time_out + 1000
                return

            elif status == S_CANCELED:
                self.race_time = self.time_out + 1000
                return

            if self.start_timestamp and time.time() > self.start_timestamp + self.time_out:
                self.race_time = self.time_out + 1000
                return

            time.sleep(.1)

    def calc_fitness_value(self):
        """
        Calculates the fitness-value based on the game-performance.
        Current elements of the fitness-value are:
            ~ time
            ~ damage
        :return: the fitness-value
        """
        # TODO evt more parameters like (total_#_checkpoints - #_passed_checkpoints)
        return self.race_time + self.damage
