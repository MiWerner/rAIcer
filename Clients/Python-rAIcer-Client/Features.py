import pygame
from ImageUtils import MIN_BALL_RADIUS
from math import sqrt
import time

MIN_DISTANCE = MIN_BALL_RADIUS


class FeatureCalculator(object):
    CALC_SPEED_DELAY = 0.1
    ball_pos_stamps = []
    last_speed = (0, 0)

    @staticmethod
    def draw_features(display, ball_pos, du, dd, dl, dr, dul, dur, ddl, ddr):
        """
        Draw lines to the obstacles in all eight directions
        :param display: current pygame screen
        :param ball_pos: position of the ball
        :param du: distance in upper direction
        :param dd: distance in lower direction
        :param dl: distance to the left
        :param dr: distance to the right
        :param dul: distance in upper left direction (list containing horizontal, vertical and total distance)
        :param dur: distance in upper right direction (list containing horizontal, vertical and total distance)
        :param ddl: distance in lower left direction (list containing horizontal, vertical and total distance)
        :param ddr: distance in lower right direction (list containing horizontal, vertical and total distance)
        :return:
        """
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0], ball_pos[1] - du),
                         (ball_pos[0], ball_pos[1]))  # dist up
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0], ball_pos[1] + dd),
                         (ball_pos[0], ball_pos[1]))  # dist down
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0] - dl, ball_pos[1]),
                         (ball_pos[0], ball_pos[1]))  # dist left
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0] + dr, ball_pos[1]),
                         (ball_pos[0], ball_pos[1]))  # dist right
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0] - dul[0], ball_pos[1] - dul[1]),
                         (ball_pos[0], ball_pos[1]))  # dist up left
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0] + dur[0], ball_pos[1] - dur[1]),
                         (ball_pos[0], ball_pos[1]))  # dist up right
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0] - ddl[0], ball_pos[1] + ddl[1]),
                         (ball_pos[0], ball_pos[1]))  # dist down left
        pygame.draw.line(display, (255, 200, 200), (ball_pos[0] + ddr[0], ball_pos[1] + ddr[1]),
                         (ball_pos[0], ball_pos[1]))  # dist down right

    def calc_speed_features(self, ball_pos):
        """
        Calculates the speed pf the ball, based on the last tow ball position and the given current ball position.
        :param ball_pos: the current position of the ball
        :return: the current horizontal and vertical speed
        """

        if not self.ball_pos_stamps:
            self.ball_pos_stamps.append((ball_pos, time.time()))
            self.last_speed = (0, 0)
            return self.last_speed

        if self.ball_pos_stamps[-1][1] > time.time() - self.CALC_SPEED_DELAY:
            return self.last_speed

        self.ball_pos_stamps.append((ball_pos, time.time()))

        if len(self.ball_pos_stamps) >= 3:
            vx = 0
            vy = 0
            combos = [(0, 1), (1, 2), (0, 2)]
            for i, j in combos:
                vx += (self.ball_pos_stamps[i][0][0] - self.ball_pos_stamps[j][0][0]) / \
                      (self.ball_pos_stamps[j][1] - self.ball_pos_stamps[i][1])
                vy += (self.ball_pos_stamps[i][0][1] - self.ball_pos_stamps[j][0][1]) / \
                      (self.ball_pos_stamps[j][1] - self.ball_pos_stamps[i][1])

            vx /= len(combos)
            vy /= len(combos)

            self.ball_pos_stamps.remove(self.ball_pos_stamps[0])
            self.last_speed = (vx, vy)
            return self.last_speed

        return self.last_speed

    def calc_distance_features(self, ball_pos, track_mask):
        """
        Calculates the distance to obstacles in eight directoins
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labled as False or 0
        :return: distance in upper direction
                 distance in lower direction
                 distance to the left
                 distance to the right
                 distance in the upper left direction (is list)
                 distance in the upper right direction (is list)
                 distance in the lower left direction (is list)
                 distance in the lower right direction (is list)
        """
        dist_up = self._calc_distance_up(ball_pos, track_mask)
        dist_down = self._calc_distance_down(ball_pos, track_mask)
        dist_left = self._calc_distance_left(ball_pos, track_mask)
        dist_right = self._calc_distance_right(ball_pos, track_mask)
        dist_up_left = self._calc_distance_up_left(ball_pos, track_mask)
        dist_up_right = self._calc_distance_up_right(ball_pos, track_mask)
        dist_down_left = self._calc_distance_down_left(ball_pos, track_mask)
        dist_down_right = self._calc_distance_down_right(ball_pos, track_mask)
        return dist_up, dist_down, dist_left, dist_right, dist_up_left, dist_up_right, dist_down_left, dist_down_right

    def _calc_distance_up(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle upwards
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0.
        :return: the distance to the next obstacle upwards
        """
        _, du, _ = self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=0, direction_y=-1)
        return du

    def _calc_distance_down(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle downwards
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0.
        :return: the distance to the next obstacle downwards
        """
        _, dd, _ = self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=0, direction_y=1)
        return dd

    def _calc_distance_left(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle on the left
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0.
        :return: the distance to the next obstacle on the left
        """
        dl, _, _ = self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=-1, direction_y=0)
        return dl

    def _calc_distance_right(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle on the right
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0.
        :return: the distance to the next obstacle on the right
        """
        dr, _, _ = self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=1, direction_y=0)
        return dr

    def _calc_distance_up_left(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle in the upper left direction
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0
        :return: the distance to the next obstacle in the upper left direction
        """
        return list(self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=-1, direction_y=-1))

    def _calc_distance_up_right(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle in the upper right direction
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0
        :return: the distance to the next obstacle in the upper right direction
        """
        return list(self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=1, direction_y=-1))

    def _calc_distance_down_right(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle in the lower right direction
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0
        :return: the distance to the next obstacle in the lower right direction
        """
        return list(self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=1, direction_y=1))

    def _calc_distance_down_left(self, ball_pos, track_mask):
        """
        Calculates the distance from the ball to the next obstacle in the lower left direction
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0
        :return: the distance to the next obstacle in the lower left direction
        """
        return list(self.__calc_distance(ball_pos=ball_pos, track_mask=track_mask, direction_x=-1, direction_y=1))

    @staticmethod
    def __calc_distance(ball_pos, track_mask, direction_x, direction_y):
        """
        Calculates the horizontal and vertical distance from the ball to the next obstacle in the direction defined by
         direction_x and direction_y
        :param ball_pos: the position of the ball
        :param track_mask: mask of the track. Obstacles are labeled as False or 0
        :param direction_x: direction of horizontal movement: -1: left, 0: no movement, 1: right
        :param direction_y: direction of vertical movement: -1: up, 0: no movement, 1: down
        :return: horizontal_distance, vertical distance, total distance
        """
        current_x = ball_pos[0] + (MIN_DISTANCE * direction_x)
        current_y = ball_pos[1] + (MIN_DISTANCE * direction_y)

        while track_mask[current_x, current_y]:
            current_x += direction_x
            current_y += direction_y
        dx = abs(ball_pos[0] - current_x) - 1
        dy = abs(ball_pos[1] - current_y) - 1

        return dx, dy, sqrt(dx ** 2 + dy ** 2)
