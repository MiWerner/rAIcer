from Utils import IMG_HEIGHT, IMG_WIDTH, print_debug
import cv2 as cv
import numpy as np

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
    cv.imshow('mask', ball_mask)

    # Get the mean position of all non-zero points in the mask to get the center of the ball
    center = np.mean(np.transpose(np.nonzero(ball_mask)), axis=0)
    return center


def get_track(img):
    # Set the bounds to detect the black parts of the track and invert it to get the actual track
    lower_bounds = np.array([0, 0, 0])
    upper_bounds = np.array([10, 10, 10])
    track = cv.bitwise_not(cv.inRange(img, lower_bounds, upper_bounds))
    # Closing (Dilate + Erode) to remove noise (of the ball border)
    track = cv.morphologyEx(track, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    image, contours, hierarchy = cv.findContours(track, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    print_debug("Contours: ", len(contours))
    for c in contours:
        print_debug("Contour-Length: ", len(c))
        print_debug("Contour:", c)

    # Draw cross sections of the track
    # TODO: Find the contour points corresponding to the start line to use them for aligning both contours
    # (instead of hardcoding a shift by 3)
    # TODO: Think of a way to use this for tracks with multiple possible ways/more than 2 contours
    number_of_sections = 50
    for i in range(0, number_of_sections):
        index1 = (i-3) * len(contours[0])//number_of_sections
        if i < 3:
            index1 = (i-3+number_of_sections) * len(contours[0])//number_of_sections

        point1 = contours[0][index1][0]
        point2 = contours[1][(number_of_sections-i-1) * len(contours[1])//number_of_sections][0]
        cv.line(image, tuple(point1), tuple(point2), (0, 0, 0))

    cv.imshow("track", track) # TODO image
    return track, image  # Not sure what to actually return later, just return anything so this does not get called again

