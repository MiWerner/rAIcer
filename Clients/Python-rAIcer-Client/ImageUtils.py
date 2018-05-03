from Utils import IMG_HEIGHT, IMG_WIDTH, print_debug
import MatrixOps
import cv2 as cv
import numpy as np

MIN_BALL_RADIUS = 5
MIN_PRIMARY_COLOR_VALUE_BALL = 100
MAX_OTHER_COLOR_VALUE_BALL = 10


def byte_array_to_image(byte_array):
    """
    Converts the byte array received from the server into a 3d numpy matrix used to represent an RGB image
    :param byte_array: the byte array
    :return: 3d matrix representing a RGB image
    """
    img = np.fromstring(byte_array, dtype=np.uint8)
    img = img.reshape(IMG_HEIGHT, IMG_WIDTH, 3)
    img = np.transpose(img, (1, 0, 2))
    img = np.flip(img, 1)  # Invert x axis
    return img


def get_ball_position(ID, img):
    """
    Finds the ball with the given id in the image and returns its center position
    :param ID: the id of the ball (1-red, 2-green or 3-blue)
    :param img: the image to search on
    :return: center position of the ball
    """

    # Set the lower bounds to MIN_PRIMARY_COLOR_VALUE_BALL for the actual color of the ball (based on the id)
    # and to 0 for the other two colors
    lower_bounds = np.array([0, 0, 0])
    lower_bounds[ID-1] = MIN_PRIMARY_COLOR_VALUE_BALL

    # Set the upper bounds to 255 for the actual color of the ball (based on the id)
    # and to MAX_OTHER_COLOR_VALUE_BALL for the two colors
    upper_bounds = np.array([MAX_OTHER_COLOR_VALUE_BALL, MAX_OTHER_COLOR_VALUE_BALL, MAX_OTHER_COLOR_VALUE_BALL])
    upper_bounds[ID-1] = 255

    # Get a binary image which only highlights the ball
    ball_mask = cv.inRange(img, lower_bounds, upper_bounds)

    # Get the mean position of all non-zero points in the mask to get the center of the ball
    center = np.flip(np.mean(cv.findNonZero(ball_mask), axis=0)[0], 0)
    return center


def get_distance_to_center(point):
    """
    Returns the Hammington distance of the given point to the window center
    :param point: the point
    :return: the Hammington distance of the given point to the window center
    """
    window_center = np.array([IMG_WIDTH/2, IMG_HEIGHT/2])
    return np.sum(np.abs(np.subtract(window_center, point)))  # Hammington distance is good enough


def get_track(img):
    """
    Creates and returns a binary image of the track. Also finds track sections and starts the calculation of the racing line
    :param img: the image
    :return: a binary image of the track
    """
    # Set the bounds to detect the black parts of the track and invert it to get the actual track
    lower_bounds_track = np.array([0, 0, 0])
    upper_bounds_track = np.array([10, 10, 10])
    track = cv.bitwise_not(cv.inRange(img, lower_bounds_track, upper_bounds_track))
    # Closing (Dilate + Erode) to remove noise (of the ball border)
    track = cv.morphologyEx(track, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    # Find the finish line
    lower_bounds_finish = np.array([200, 100, 0])
    upper_bounds_finish = np.array([255, 150, 10])
    finish_line = cv.dilate(cv.inRange(img, lower_bounds_finish, upper_bounds_finish), np.ones((5, 5), np.uint8),
                            iterations=1)
    finish_line_coords = cv.findNonZero(finish_line)
    finish_line_center = np.flip(np.mean(finish_line_coords, axis=0)[0], 0)

    # Get the contours of the track
    _, contours, hierarchy = cv.findContours(track, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    image = track.copy()

    # Get the inner and outer contour and the indices of the points where they touch the finish line
    inner_contour, outer_contour, inner_start_index, outer_start_index = _get_inner_and_outer_contour(contours, finish_line_coords)

    # Calculate the starting direction based on the center of the actual start line and center of the orange area
    direction = finish_line_center - MatrixOps.convex_combination(inner_contour[inner_start_index][0], outer_contour[outer_start_index][0], 0.5, True)

    # Calculate cross sections of the track
    number_of_sections = 50
    sections = np.empty([number_of_sections, 2, 2], dtype=int)
    for i in range(0, number_of_sections):
        # Indices have different signs in their calculation because on goes clockwise
        # and the other one goes counter-clockwise
        inner_index = (inner_start_index + i*len(inner_contour)//number_of_sections) % len(inner_contour)
        outer_index = (outer_start_index - i*len(outer_contour)//number_of_sections) % len(outer_contour)
        sections[i][0] = inner_contour[inner_index][0]
        sections[i][1] = outer_contour[outer_index][0]
        cv.line(image, tuple(sections[i][0]), tuple(sections[i][1]), (0, 0, 0))

    cv.imshow("track", image)
    return track  # Not sure what to actually return later, just return anything so this does not get called again


def _get_inner_and_outer_contour(contours, finish_line_coords):
    """
    Finds the contours that touch the start/finish line and returns them as inner and outer contour
    as well as the index of the point where the start/finish line touches the contour
    :param contours: all found contours
    :param finish_line_coords: array containing all coordinates of the finish line
    :return: the inner and outer contour and the indices of the points where they touch the finish line
    """
    inner_contour = None
    outer_contour = None
    inner_start_index = None
    outer_start_index = None
    for c in contours:
        # Find all intersecting points of finish line and contour
        intersection = MatrixOps.multidim_intersect(c, finish_line_coords)
        if intersection.any():
            # If there is ar intersecting points, get the median point and find their index
            median_intersection = intersection[int(len(intersection) / 2)]
            intersection_index = MatrixOps.multidim_indexof(c, median_intersection)

            # Determine if the found point belongs to the inner or outer contour and set it accordingly
            if inner_start_index is None:
                inner_contour = c
                inner_start_index = intersection_index
            else:
                if get_distance_to_center(median_intersection) < get_distance_to_center(
                        inner_contour[inner_start_index]):
                    outer_contour = inner_contour
                    inner_contour = c
                    outer_start_index = inner_start_index
                    inner_start_index = intersection_index
                else:
                    outer_contour = c
                    outer_start_index = intersection_index
    return inner_contour, outer_contour, inner_start_index, outer_start_index
