import pygame
from ImageUtils import MIN_BALL_RADIUS, get_ball_position, get_track
from math import sqrt
import time
import numpy as np

MIN_DISTANCE = MIN_BALL_RADIUS
NUM_STAMPS_CALC_SPEED = 7
COLORS = [(255, 200, 200), (200, 255, 200), (200, 200, 255)]

DIRECTIONS =[
    ( 0, -1),  # up
    ( 1, -1),  # up right
    ( 1,  0),  # right
    ( 1,  1),  # down right
    ( 0,  1),  # down
    (-1,  1),  # down left
    (-1,  0),  # left
    (-1, -1),  # up left
]


class FeatureCalculator(object):

    ball_pos_stamps = []  # list of past NUM_STAMPS_CALC_SPEED ball-positions and time stamps
    dist_features = (0, ) * 8  # distance feature vector
    speed_features = (0, 0)  # speed feature vector
    ball_mask = None  # map for detected opponents, used for distances

    def __init__(self, client_id, img, max_clients=3):
        self.track, _ = get_track(img=img)  # map of the track
        self.client_id = client_id  # id of coresponding client
        self.max_clients = max_clients  # maximum number of clients. Used for opponent detection

    @property
    def features(self):
        """
        Returns a feature vector in the following order
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
        f = ()
        for i, d in enumerate(self.dist_features):
            if i % 2 == 1:
                try:
                    d = d[2]
                except TypeError:
                    pass
            f += (d, )
        f += self.speed_features
        return f

    def update(self, img, print_features=False):
        """
        Calculates new features based on the new image.
        :param img: a new image.
        :param print_features: if True the new feature values are printed
        :return:
        """
        bp, _ = get_ball_position(ID=self.client_id, img=img)
        bp = tuple(map(int, bp))
        self.ball_pos_stamps.append((bp, time.time()))

        if len(self.ball_pos_stamps) > NUM_STAMPS_CALC_SPEED:
            self.ball_pos_stamps.remove(self.ball_pos_stamps[0])

        self.ball_mask = np.zeros(np.shape(self.track))
        for i in range(1, self.max_clients + 1):
            try:
                if not i == self.client_id:
                    _, m = get_ball_position(i, img)
                    self.ball_mask += m
            except IndexError:
                # if an opponent was not found
                self.max_clients = i - 1
                break

        self._calc_distance_features()

        self._calc_speed_features()

        if print_features:
            self.print_features()

    def print_features(self):
        """
        Prints all feature values.
        :return:
        """
        print("ID {}: du={} | dur={} | dr={} | ddr={} | dd={} | ddl={} | dl={} | dul={} | vx={} | vy={}"
              .format(self.client_id,
                      *tuple(map(lambda x: str(int(x)).zfill(4), self.features))))

    def draw_features(self, display):
        """
        Draw lines to the obstacles in all eight directions
        :return:
        """
        ball_pos = self.ball_pos_stamps[-1][0]
        c = COLORS[self.client_id - 1]
        # dist up
        self.__draw_line(display, c, ball_pos, 0, -self.dist_features[0])
        # dist up right
        self.__draw_line(display, c, ball_pos, self.dist_features[1][0], -self.dist_features[1][1])
        # dist right
        self.__draw_line(display, c, ball_pos, self.dist_features[2], 0)
        # dist down right
        self.__draw_line(display, c, ball_pos, self.dist_features[3][0], self.dist_features[3][1])
        # dist down
        self.__draw_line(display, c, ball_pos, 0, self.dist_features[4])
        # dist down left
        self.__draw_line(display, c, ball_pos, -self.dist_features[5][0], self.dist_features[5][1])
        # dist left
        self.__draw_line(display, c, ball_pos, -self.dist_features[6], 0)
        # dist up left
        self.__draw_line(display, c, ball_pos, -self.dist_features[7][0], -self.dist_features[7][1])

        # speed
        self.__draw_line(display, (200, 255, 200), ball_pos, self.speed_features[0], self.speed_features[1])

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
