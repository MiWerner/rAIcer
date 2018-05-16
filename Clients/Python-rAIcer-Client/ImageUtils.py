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
    return center, ball_mask


def get_distance_to_center(point):
    """
    Returns the Manhattan distance of the given point to the window center
    :param point: the point
    :return: the Manhattan distance of the given point to the window center
    """
    window_center = np.array([IMG_HEIGHT/2, IMG_WIDTH/2])
    return np.sum(np.abs(np.subtract(window_center, point)))  # Manhattan distance is good enough


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
    finish_line_center = np.mean(finish_line_coords, axis=0)[0]

    # Get the contours of the track
    _, contours, _ = cv.findContours(track, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    image = track.copy()

    # Get the inner and outer contour and the indices of the points where they touch the finish line
    inner_contour, outer_contour, inner_start_index, outer_start_index, inner_contour_index = _get_inner_and_outer_contour(contours, finish_line_coords)

    # Calculate the starting direction based on the center of the actual start line and center of the orange area
    direction = finish_line_center - MatrixOps.convex_combination(inner_contour[inner_start_index], outer_contour[outer_start_index], 0.5)
    direction = direction / np.linalg.norm(direction)

    ### Calculate cross sections of the track ###
    # Create empty/black 3-channel image to run watershed on
    img_empty = np.zeros(img.shape, np.uint8)
    # Create a 1-channel image for the markers
    markers = np.zeros(image.shape, np.int32)
    # Mark the inner contour with label 1 and the other contours with label 2 by drawing them on the markers image
    for i in range(0, len(contours)):
        cv.drawContours(markers, contours, i, 1 if i == inner_contour_index else 2)
    # Use watershed to get the boundary between inner and outer contour
    markers = cv.watershed(img_empty, markers)
    # Remove '-1' markers on the border of the image
    markers[:, 0] = markers[1, 1]
    markers[0, :] = markers[1, 1]
    markers[:, -1] = markers[1, 1]
    markers[-1, :] = markers[1, 1]

    # Get a sorted vector of all positions of points on the watershed border
    _, watershed_contours, _ = cv.findContours((markers == -1).astype(np.uint8), cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    watershed_contour = watershed_contours[0].reshape(len(watershed_contours[0]), 2)

    img[markers == -1] = [0, 0, 255]

    # cv.imshow("color", img) TODO remove #

    # Circshift the contour so that the first point corresponds to the start/finishing line
    start_index = MatrixOps.find_closest_point_index(MatrixOps.convex_combination(inner_contour[inner_start_index], outer_contour[outer_start_index], 0.5), watershed_contour)
    watershed_contour = np.roll(watershed_contour, -2*start_index)

    # Check if flipping the contour array is necessary based on the start direction
    next_point = watershed_contour[0] + direction
    closest_point_index = MatrixOps.find_closest_point_index(next_point, watershed_contour[[1, len(watershed_contour)-1]])
    if closest_point_index == 1:
        watershed_contour = np.flip(watershed_contour, 0)

    # cv.imshow("image", image) TODO remove #
    return track, watershed_contour


def _get_inner_and_outer_contour(contours, finish_line_coords):
    """
    Finds the contours that touch the start/finish line and returns them as inner and outer contour
    as well as the index of the point where the start/finish line touches the contour
    :param contours: all found contours
    :param finish_line_coords: array containing all coordinates of the finish line
    :return: the inner and outer contour and the indices of the points where they touch the finish line as well as a
    combined list of all contours except the inner one
    """
    inner_contour_index = -1
    inner_contour = None
    outer_contour = None
    other_contours = np.array([], dtype=int).reshape(0, 2)
    inner_start_index = None
    outer_start_index = None
    for i in range(0, len(contours)):
        c = contours[i]
        # Find all intersecting points of finish line and contour
        intersection = MatrixOps.multidim_intersect(c, finish_line_coords)
        if intersection.any():
            # If there is ar intersecting points, get the median point and find their index
            median_intersection = intersection[int(len(intersection) / 2)]
            intersection_index = MatrixOps.multidim_indexof(c.reshape(len(c), 2), median_intersection)

            # Determine if the found point belongs to the inner or outer contour and set it accordingly
            if inner_start_index is None:
                inner_contour = c
                inner_contour_index = i
                inner_start_index = intersection_index
            else:
                if get_distance_to_center(median_intersection) < get_distance_to_center(inner_contour[inner_start_index]):
                    outer_contour = inner_contour
                    inner_contour = c
                    inner_contour_index = i
                    outer_start_index = inner_start_index
                    inner_start_index = intersection_index
                    other_contours = np.r_[other_contours, outer_contour.reshape(len(outer_contour), 2)]
                else:
                    outer_contour = c
                    outer_start_index = intersection_index
                    other_contours = np.r_[other_contours, c.reshape(len(c), 2)]
        else:
            other_contours = np.r_[other_contours, c.reshape(len(c), 2)]
    return inner_contour.reshape(len(inner_contour), 2), outer_contour.reshape(len(outer_contour), 2), inner_start_index, outer_start_index, inner_contour_index


def _draw_racing_line(image, sections, values):
    for i in range(0, len(sections)):
        point1 = MatrixOps.convex_combination(sections[i][0], sections[i][1], values[i])
        index_next = (i+1) % len(sections)
        point2 = MatrixOps.convex_combination(sections[index_next][0], sections[index_next][1], values[index_next])
        cv.line(image, tuple(point1.astype(int)), tuple(point2.astype(int)), (0, 0, 0))
