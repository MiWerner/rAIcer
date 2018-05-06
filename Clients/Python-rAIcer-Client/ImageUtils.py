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
    Returns the Hamming distance of the given point to the window center
    :param point: the point
    :return: the Hamming distance of the given point to the window center
    """
    window_center = np.array([IMG_HEIGHT/2, IMG_WIDTH/2])
    return np.sum(np.abs(np.subtract(window_center, point)))  # Hamming distance is good enough


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

    # Init and draw the racing line
    racing_line_values = np.zeros([number_of_sections])
    ANGLE_FACTOR = 100
    ITERATIONS = 50
    for k in range(0, ITERATIONS):
        for i in range(0, number_of_sections):
            # Get the points around the current one and the vectors between them
            previous_previous_index = (i-2) % number_of_sections
            previous_index = (i-1) % number_of_sections
            next_index = (i+1) % number_of_sections
            next_next_index = (i+2) % number_of_sections
            point0 = MatrixOps.convex_combination(sections[previous_previous_index][0], sections[previous_previous_index][1], racing_line_values[previous_previous_index])
            point1 = MatrixOps.convex_combination(sections[previous_index][0], sections[previous_index][1], racing_line_values[previous_index])
            point3 = MatrixOps.convex_combination(sections[next_index][0], sections[next_index][1], racing_line_values[next_index])
            point4 = MatrixOps.convex_combination(sections[next_next_index][0], sections[next_next_index][1], racing_line_values[next_next_index])
            vector0 = point1 - point0
            vector3 = point4 - point3
            norm0 = np.linalg.norm(vector0)
            norm3 = np.linalg.norm(vector3)

            smallest_value = -1
            # Only check a few values around the current one per iteration
            steps = [racing_line_values[i]]
            for j in range(1, 6):
                if racing_line_values[i] + j*0.01 <= 1.0:
                    steps.append(racing_line_values[i] + j*0.01)
                else:
                    break
            for j in range(1, 11):
                if racing_line_values[i] - j*0.01 >= 0:
                    steps.append(racing_line_values[i] - j*0.01)
                else:
                    break

            for j in range(0, len(steps)):
                # Try out different points for the current section and get the vectors accordingly
                point2 = MatrixOps.convex_combination(sections[i][0], sections[i][1], steps[j])
                vector1 = point2 - point1
                vector2 = point3 - point2
                norm1 = np.linalg.norm(vector1)
                norm2 = np.linalg.norm(vector2)

                # Calculate the distance of the vectors and the angles between them
                dist0 = norm0 + norm1
                dist1 = norm1 + norm2
                dist2 = norm2 + norm3
                angle0 = -np.clip(np.dot(vector0/norm0, vector1/norm1), -1.0, 1.0)
                angle1 = -np.clip(np.dot(vector1/norm1, vector2/norm2), -1.0, 1.0)
                angle2 = -np.clip(np.dot(vector2/norm2, vector3/norm3), -1.0, 1.0)

                # The actual evaluation function for the current point of the racing line (smaller -> better)
                new_value = dist1 + ANGLE_FACTOR * (angle0/dist0 + angle1/dist1 + angle2/dist2)

                if new_value < smallest_value or smallest_value < 0:
                    smallest_value = new_value
                    racing_line_values[i] = steps[j]

    _draw_racing_line(image, sections, racing_line_values)

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


def _draw_racing_line(image, sections, values):
    for i in range(0, len(sections)):
        point1 = MatrixOps.convex_combination(sections[i][0], sections[i][1], values[i])
        index_next = (i+1) % len(sections)
        point2 = MatrixOps.convex_combination(sections[index_next][0], sections[index_next][1], values[index_next])
        cv.line(image, tuple(point1.astype(int)), tuple(point2.astype(int)), (0, 0, 0))
