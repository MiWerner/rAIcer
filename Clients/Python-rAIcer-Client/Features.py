import pygame
from ImageUtils import MIN_BALL_RADIUS

MIN_DISTANCE = MIN_BALL_RADIUS


def draw_features(display, ball_pos, du, dd, dl, dr):
    pygame.draw.line(display, (255, 200, 200), (ball_pos[0], ball_pos[1] - du),
                     (ball_pos[0], ball_pos[1]))  # dist up
    pygame.draw.line(display, (255, 200, 200), (ball_pos[0], ball_pos[1] + dd),
                     (ball_pos[0], ball_pos[1]))  # dist down
    pygame.draw.line(display, (255, 200, 200), (ball_pos[0] - dl, ball_pos[1]),
                     (ball_pos[0], ball_pos[1]))  # dist left
    pygame.draw.line(display, (255, 200, 200), (ball_pos[0] + dr, ball_pos[1]),
                     (ball_pos[0], ball_pos[1]))  # dist right


def calc_speed_features(last_ball_pos, ball_pos):
    if last_ball_pos is None:
        return 0, 0

    # Very inaccurate and unreliable because images come too often and not at a constant frequency
    vx = ball_pos[0] - last_ball_pos[0]
    vy = ball_pos[1] - last_ball_pos[1]
    return vx, vy


def calc_distance_features(ball_pos, track_mask):
    dist_up = _calc_distance_up(ball_pos, track_mask)
    dist_down = _calc_distance_down(ball_pos, track_mask)
    dist_left = _calc_distance_left(ball_pos, track_mask)
    dist_right = _calc_distance_right(ball_pos, track_mask)
    return dist_up, dist_down, dist_left, dist_right


def _calc_distance_up(ball_pos, track_mask):
    """
    Calculates the distance from the ball to the next obstacle upwards
    :param ball_pos: the position of the ball
    :param track_mask: mask of the track. Obstacles are labeled as False or 0.
    :return: the distance to the next obstacle upwards
    """
    current_y = ball_pos[1] - MIN_DISTANCE

    while track_mask[ball_pos[0], current_y]:
        current_y -= 1

    return ball_pos[1] - current_y - 1 # ball_pos[1] is larger or equal to current_y


def _calc_distance_down(ball_pos, track_mask):
    """
    Calculates the distance from the ball to the next obstacle downwards
    :param ball_pos: the position of the ball
    :param track_mask: mask of the track. Obstacles are labeled as False or 0.
    :return: the distance to the next obstacle downwards
    """
    current_y = ball_pos[1] + MIN_DISTANCE

    while track_mask[ball_pos[0], current_y]:
        current_y += 1

    return current_y - ball_pos[1] - 1  # current_y is larger or equal to ball_pos[1]


def _calc_distance_left(ball_pos, track_mask):
    """
    Calculates the distance from the ball to the next obstacle on the left
    :param ball_pos: the position of the ball
    :param track_mask: mask of the track. Obstacles are labeled as False or 0.
    :return: the distance to the next obstacle on the left
    """
    current_x = ball_pos[0] - MIN_DISTANCE

    while track_mask[current_x, ball_pos[1]]:
        current_x -= 1

    return ball_pos[0] - current_x - 1  # ball_pos[0] is larger or equal to current_x


def _calc_distance_right(ball_pos, track_mask):
    """
    Calculates the distance from the ball to the next obstacle on the right
    :param ball_pos: the position of the ball
    :param track_mask: mask of the track. Obstacles are labeled as False or 0.
    :return: the distance to the next obstacle on the right
    """
    current_x = ball_pos[0] + MIN_DISTANCE

    while track_mask[current_x, ball_pos[1]]:
        current_x += 1

    return current_x - ball_pos[0] - 1  # current_x is larger or equal to ball_pos[0]

