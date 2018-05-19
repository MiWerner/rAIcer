import pygame
from ImageUtils import MIN_BALL_RADIUS, get_ball_position, get_track
from MatrixOps import find_closest_point_index
from Utils import EN_HV_DIST, EN_DIAG_DIST, EN_SPEED, EN_BALLPOS, NUM_CP_FEATURES, feature_print_string, print_debug
from math import sqrt
import time
import numpy as np

MIN_DISTANCE = MIN_BALL_RADIUS
NUM_STAMPS_CALC_SPEED = 7
COLORS = [(255, 200, 200), (200, 255, 200), (200, 200, 255)]
NUM_SECTION_JUMP = 5

DIRECTIONS = [
    (0, -1),  # up
    (1, -1),  # up right
    (1,  0),  # right
    (1,  1),  # down right
    (0,  1),  # down
    (-1,  1),  # down left
    (-1,  0),  # left
    (-1, -1),  # up left
]


class FeatureCalculator(object):

    ball_pos_stamps = []  # list of past NUM_STAMPS_CALC_SPEED ball-positions and time stamps
    dist_features = (0, ) * 8  # distance feature vector
    speed_features = (0, 0)  # speed feature vector
    ball_mask = None  # map for detected opponents, used for distances
    current_section_id = 0
    last_seen_section = 0
    __features = None
    features_changed = False
    opponents_ids = []

    def __init__(self, client_id, img, max_clients=3):
        self.track, checkpoints = get_track(img=img)  # map of the track

        self.checkpoints, self.section_counter, self.checkpoint_map = self.create_sections(checkpoints)
        self.num_checkpoints = len(self.checkpoints)

        self.client_id = client_id  # id of coresponding client
        self.max_clients = max_clients  # maximum number of clients. Used for opponent detection
        for i in range(max_clients):
            if not i+1 == client_id:
                self.opponents_ids.append(i+1)

    def create_sections(self, checkpoints):
        """
        Creates reduces the number of checkpoints, creates a map with section areas and a counter for each section
        :param checkpoints: points created by watershead algorightm
        :return: final set of checkpoints, list of counters for each section, map of section
        """
        # create map for constant computing of the current sector
        s = np.shape(self.track)
        # reduce number of checkpoints and convert it to pygame format
        checkpoints = checkpoints[::20]
        checkpoint_map = np.ones(s, dtype=np.int) * len(checkpoints)
        for i in range(s[0]):
            for j in range(s[1]):
                if self.track[i, j]:  # if current point is not an obstacle
                    checkpoint_map[i, j] = int(find_closest_point_index((j, i), checkpoints))

        # flip x and y axis
        checkpoints = np.flip(checkpoints, axis=1)
        section_counter = [0] * len(checkpoints)

        return checkpoints, section_counter, checkpoint_map

    @property
    def features(self):
        """
        Returns a feature vector (tuple) in the following order
         ~ distance up
         ~ distance up right
         ~ distance right
         ~ distance down right
         ~ distance down
         ~ distance down left
         ~ distance left
         ~ distance up left
         ~ speed horizontal
         ~ speed vertical
        :return: current feature vector
        """
        if not self.features_changed:
            return self.__features

        f = ()
        # distance features
        for i, d in enumerate(self.dist_features):
            if i % 2 == 1 and EN_DIAG_DIST:
                # extract total distance for diagonal features
                try:
                    f += (d[2], )
                except TypeError:
                    pass
            elif i % 2 == 0 and EN_HV_DIST:
                f += (d, )

        # speed features
        if EN_SPEED:
            f += self.speed_features

        # current ball_position
        if EN_BALLPOS:
            f += self.ball_pos_stamps[-1][0]

        # checkpoints
        for i in range(1, NUM_CP_FEATURES+1):
            dx = self.checkpoints[(self.current_section_id + i) % self.num_checkpoints][0] - self.ball_pos_stamps[-1][0][0]
            dy = self.checkpoints[(self.current_section_id + i) % self.num_checkpoints][1] - self.ball_pos_stamps[-1][0][1]
            f += (dx, dy)

        self.__features = f
        self.features_changed = False
        return f

    def update(self, img, print_features=False):
        """
        Calculates new features based on the new image.
        :param img: a new image.
        :param print_features: if True the new feature values are printed
        :return:
        """
        self.features_changed = True

        # extract new ball position
        try:
            bp, _ = get_ball_position(ID=self.client_id, img=img)
            bp = tuple(map(int, bp))
            self.ball_pos_stamps.append((bp, time.time()))
        except IndexError:
            print_debug("ID {} did not found it self..........".format(self.client_id))
            pass

        if len(self.ball_pos_stamps) > NUM_STAMPS_CALC_SPEED:
            self.ball_pos_stamps.remove(self.ball_pos_stamps[0])

        # extract mask for the opponents
        self.ball_mask = np.zeros(np.shape(self.track))
        for i in self.opponents_ids:
            try:
                _, m = get_ball_position(i, img)
                self.ball_mask += m
            except IndexError:
                # if an opponent was not found the number of clients is known
                self.max_clients = i - 1
                self.opponents_ids.remove(i)
                break

        # ~~~~~~~~~~~~~~~~~~~~~~~~ extract new features ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # distance
        self._calc_distance_features()

        # speed
        self._calc_speed_features()

        # sections
        bp_section = self.checkpoint_map[bp[0], bp[1]]

        # check if a new section is entered
        if not bp_section == self.last_seen_section:

            # check is a new best section is entered
            # allow skipping of NUM_SECTION_JUMP sections
            r1 = range(self.current_section_id+1, self.current_section_id+NUM_SECTION_JUMP)
            r1 = list(map(lambda x: x % self.num_checkpoints, r1))

            r2 = range(self.last_seen_section + 1, self.last_seen_section + NUM_SECTION_JUMP)
            r2 = list(map(lambda x: x % self.num_checkpoints, r2))
            if bp_section in r1 and bp_section in r2:
                self.section_counter[bp_section] += 1
                # ensure over jumped section also increase counter
                i = bp_section - 1
                while i >= 0 and self.section_counter[i] < self.section_counter[bp_section]:
                    self.section_counter[i] += 1
                    i -= 1
                self.current_section_id = bp_section

        self.last_seen_section = bp_section

        if print_features:
            self.print_features()

    def print_features(self):
        """
        Prints all feature values.
        :return:
        """
        print(feature_print_string.format(self.client_id,
                                          *tuple(map(lambda x: str(int(x)).zfill(4), self.features))))

    def draw_features(self, display):
        """
        Draw lines to the obstacles in all eight directions
        :return:
        """
        ball_pos = self.ball_pos_stamps[-1][0]
        c = COLORS[self.client_id - 1]

        if EN_HV_DIST:
            # dist up
            self.__draw_line(display, c, ball_pos, 0, -self.dist_features[0])
            # dist right
            self.__draw_line(display, c, ball_pos, self.dist_features[2], 0)
            # dist down
            self.__draw_line(display, c, ball_pos, 0, self.dist_features[4])
            # dist left
            self.__draw_line(display, c, ball_pos, -self.dist_features[6], 0)

        if EN_DIAG_DIST:
            # dist up right
            self.__draw_line(display, c, ball_pos, self.dist_features[1][0], -self.dist_features[1][1])
            # dist down right
            self.__draw_line(display, c, ball_pos, self.dist_features[3][0], self.dist_features[3][1])
            # dist down left
            self.__draw_line(display, c, ball_pos, -self.dist_features[5][0], self.dist_features[5][1])
            # dist up left
            self.__draw_line(display, c, ball_pos, -self.dist_features[7][0], -self.dist_features[7][1])

        if EN_SPEED:
            # speed
            self.__draw_line(display, (200, 255, 200), ball_pos, self.speed_features[0], self.speed_features[1])

        # checkpoints
        for c in self.checkpoints:
            pygame.draw.circle(display, (200, 200, 200), c, 3)

        pygame.draw.circle(display, (200, 200, 0), self.checkpoints[self.current_section_id], 3)
        for i in range(1, NUM_CP_FEATURES+1):
            pygame.draw.circle(display, (200, 0, 200),
                               self.checkpoints[(self.current_section_id + i) % self.num_checkpoints], 3)

    @staticmethod
    def __draw_line(display, color, ball_pos, dx, dy):
        """
        Interface to the draw line function of pygame. Draws a line
        :param display: the current pygame screen
        :param color: the color of the line
        :param ball_pos: the position of the ball. Start point of the line
        :param dx: offset in vertical direction from the ball
        :param dy: offset in horizontal direction from the ball
        :return:
        """
        pygame.draw.line(display, color, ball_pos, (ball_pos[0] + dx, ball_pos[1] + dy), 2)

    def _calc_speed_features(self):
        """
        Calculates the speed pf the ball, based on the last tow ball position and the given current ball position.
        :return: the current horizontal and vertical speed
        """
        if len(self.ball_pos_stamps) >= NUM_STAMPS_CALC_SPEED:
            vx = 0
            vy = 0
            counter = 0
            for i in range(NUM_STAMPS_CALC_SPEED):
                for j in range(i+1, NUM_STAMPS_CALC_SPEED):
                    bps_i = self.ball_pos_stamps[i]
                    bps_j = self.ball_pos_stamps[j]
                    vx += (bps_j[0][0] - bps_i[0][0]) / (bps_j[1] - bps_i[1])
                    vy += (bps_j[0][1] - bps_i[0][1]) / (bps_j[1] - bps_i[1])
                    counter += 1

            vx /= counter
            vy /= counter

            self.speed_features = (vx, vy)

    def _calc_distance_features(self):
        """
        Calculates the distance to obstacles in eight directions
        :return:
        """
        d = ()
        for dx, dy in DIRECTIONS:
            if dx and dy:
                d += (list(self.__calc_distance(direction_x=dx, direction_y=dy)), )
            elif dx:
                tmp, _, _ = self.__calc_distance(direction_x=dx, direction_y=dy)
                d += (tmp, )
            elif dy:
                _, tmp, _ = self.__calc_distance(direction_x=dx, direction_y=dy)
                d += (tmp, )
        self.dist_features = d

    def __calc_distance(self, direction_x, direction_y):
        """
        Calculates the horizontal and vertical distance from the ball to the next obstacle in the direction defined by
         direction_x and direction_y
        :param direction_x: direction of horizontal movement: -1: left, 0: no movement, 1: right
        :param direction_y: direction of vertical movement: -1: up, 0: no movement, 1: down
        :return: horizontal_distance, vertical distance, total distance
        """
        ball_pos = self.ball_pos_stamps[-1][0]
        current_x = ball_pos[0] + (MIN_DISTANCE * direction_x)
        current_y = ball_pos[1] + (MIN_DISTANCE * direction_y)

        while self.track[current_x, current_y] and not self.ball_mask[current_x, current_y]:
            current_x += direction_x
            current_y += direction_y
        dx = abs(ball_pos[0] - current_x) - 1
        dy = abs(ball_pos[1] - current_y) - 1

        return dx, dy, sqrt(dx ** 2 + dy ** 2)
