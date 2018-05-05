import RaicerSocket
import neat
from threading import Thread
from ImageUtils import get_ball_position, get_track
from Features import FeatureCalculator
import numpy as np
from Utils import S_WAIT, S_COUNTDOWN, S_RUNNING, S_FINISHED, S_CANCELED, S_CRASHED
import time


class GenomeEvaluator(object):

    time_out = 4*60  # s  (maximum time for one run)

    start_timestamp = None

    race_time = None

    damage = None

    is_connected = False

    is_finished = False

    def __init__(self):
        self.socket = RaicerSocket.RaicerSocket()
        self.thread = None
        self.fc = FeatureCalculator()
        self.track = None

    def run(self, genome_id, genome, config, out_q):
        """
        Starts the connection to the server. Then runs the genome of this evaluator as a Client.
        When the game is over the connection is closed and the fitness-value saved in the given output-queue
        :param genome_id: the id of the corresponding genome in the current generation
        :param genome: the corresponding genome
        :param config: the current configuration
        :param out_q: Queue where the fitness-value of the genome is stored
        :return:
        """
        self.socket.connect()
        net = neat.nn.FeedForwardNetwork.create(genome=genome, config=config)  # TODO evt also RNN
        self.__client_logic(net=net)
        self.socket.close()
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
        while not self.is_finished:
            # wait for a new message
            while not self.socket.new_message:
                time.sleep(.2)

            # receive new message
            client_id, status, lap_id, lap_total, damage, rank, image = self.socket.receive()

            if damage is not None:
                self.damage = damage

            if status == S_WAIT:
                # wait for game to start
                if not self.is_connected:
                    self.is_connected = True

            elif status == S_COUNTDOWN:
                # extract track during countdown
                if self.track is None:
                    self.track = get_track(img=image)

            elif status == S_RUNNING:
                if self.start_timestamp is None:
                    # set timestamp when race stated for fitness calculation
                    self.start_timestamp = time.time()

                # extract features
                ball_pos = np.asarray(get_ball_position(ID=client_id, img=image), dtype=np.int64)
                du, dd, dl, dr, dul, dur, ddl, ddr = self.fc.calc_distance_features(ball_pos=ball_pos,
                                                                                    track_mask=self.track)
                vx, vy = self.fc.calc_speed_features(ball_pos=ball_pos)
                # TODO include idle-line features
                inputs = np.asarray([du, dur[2], dr, ddr[2], dd, ddl[2], dl, dul[2], vx, vy], dtype=np.int64)

                # calculate key strokes
                output_f = net.activate(inputs=inputs)

                output = np.asarray(np.asarray(output_f) + np.asarray([.5 for _ in range(len(output_f))]),
                                    dtype=np.int8)
                print("ID {}: {} | {}".format(client_id, output, output_f))

                # send keys strokes to server
                self.socket.send(output[0], output[1], output[2], output[3])

                # TODO evt. save more statistics for fitness-value

            elif status == S_FINISHED:
                # save time of racing
                self.race_time = time.time() - self.start_timestamp
                self.is_finished = True
                return

            elif status == S_CRASHED:
                # client broke
                # TODO think about different  punishment
                self.race_time = self.time_out + 1000
                self.is_finished = True
                return

            elif status == S_CANCELED:
                self.race_time = self.time_out + 1000
                self.is_finished = True
                return

            if self.start_timestamp and time.time() > self.start_timestamp + self.time_out:
                self.race_time = self.time_out + 1000
                self.is_finished = True
                return

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
