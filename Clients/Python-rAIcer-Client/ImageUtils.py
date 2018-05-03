from Utils import IMG_HEIGHT, IMG_WIDTH, print_debug
import cv2 as cv
import numpy as np
import time

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
    window_center = np.array([IMG_WIDTH/2, IMG_HEIGHT/2])
    return np.sum(np.abs(np.subtract(window_center, point)))  # Hammington distance is good enough


def get_track(img):
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

    _, contours, hierarchy = cv.findContours(track, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    image = track.copy()

    inner_contour = None
    outer_contour = None
    inner_start_index = None
    outer_start_index = None
    for c in contours:
        print_debug("Contour-Length: ", len(c))
        print_debug("Contour:", c)
        intersection = multidim_intersect(c, finish_line_coords)
        if intersection.any():
            median_intersection = intersection[int(len(intersection)/2)]
            intersection_index = multidim_indexof(c, median_intersection)

            if inner_start_index is None:
                inner_contour = c
                inner_start_index = intersection_index
            else:
                if get_distance_to_center(median_intersection) < get_distance_to_center(inner_contour[inner_start_index]):
                    outer_contour = inner_contour
                    inner_contour = c
                    outer_start_index = inner_start_index
                    inner_start_index = intersection_index
                else:
                    outer_contour = c
                    outer_start_index = intersection_index

    # Calculate the starting direction based on the center of the actual start line and center of the orange area
    direction = finish_line_center - convex_combination(inner_contour[inner_start_index][0], outer_contour[outer_start_index][0], 0.5, True)

    # Draw cross sections of the track
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

    # image and track seem to be the same image
    cv.imshow("track", image)
    return track  # Not sure what to actually return later, just return anything so this does not get called again


def multidim_intersect(arr1, arr2):
    # Remove third dimension from the arrays
    arr1 = arr1.reshape(len(arr1), 2)
    arr2 = arr2.reshape(len(arr2), 2)
    # Change the inner arrays to tuples to compare them
    arr1_view = arr1.view([('', arr1.dtype)]*arr1.shape[1])
    arr2_view = arr2.view([('', arr2.dtype)]*arr2.shape[1])
    # Find the intersections and return them
    intersected = np.intersect1d(arr1_view, arr2_view)
    return intersected.view(arr1.dtype).reshape(-1, arr1.shape[1])


def multidim_indexof(array, element):
    # Maybe improve performance later? The numpy variants do not seem to work though
    for i in range(0, len(array)):
        if np.array_equal(array[i][0], element):
            return i
    return -1


def convex_combination(point1, point2, factor=0.5, flip=False):
    result = point1*factor + point2*(1-factor)
    return np.flip(result, 0) if flip else result



