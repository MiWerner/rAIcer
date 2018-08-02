import numpy as np
import math


def multidim_intersect(arr1, arr2):
    """
    Finds and returns all points that are present in both arrays
    :param arr1: the first array
    :param arr2: the second array
    :return: an array of all points that are present in both arrays
    """
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
    """
    Finds and returns the index of the first occurrence of element in array
    :param array: the first array
    :param element: the element to find
    :return: the index of the first occurrence of element in array
    """
    # Maybe improve performance later? The numpy variants do not seem to work though
    for i in range(0, len(array)):
        if np.array_equal(array[i], element):
            return i
    return -1


def convex_combination(point1, point2, factor=0.5, flip=False):
    """
    Calculates the convex combination of two points with a given factor and returns the resulting point
    which optionally flipped
    :param point1: the first point
    :param point2: the second point
    :param factor: the factor for the first point
    :param flip: whether the resulting point should be flipped
    :return: the convex combination of both points
    """
    result = point1*factor + point2*(1-factor)
    return np.flip(result, axis=0) if flip else result


def fast_norm(vector):
    """
    Calculates the norm of the given (numpy) vector(s) using standard math library instead of numpy because it is faster
    on single vectors
    :param vector: the vector
    :return: the norm(s) of the vector(s)
    """
    if hasattr(vector, "ndim") and vector.ndim == 2:
        n = len(vector)
        norms = np.zeros(n)
        for i in range(n):
            norms[i] = math.sqrt(vector[i][0]**2 + vector[i][1]**2)
        return norms

    return math.sqrt(vector[0]**2 + vector[1]**2)


def angle_between_vectors(vector1, vector2):
    """
    Calculates the angle in radians between two vectors by taking the dot product of their unit vectors
    :param vector1: the first vector
    :param vector2: the second vector
    :return: the angle in radians between both vectors
    """
    vector1 = vector1 / fast_norm(vector1)
    vector2 = vector2 / fast_norm(vector2)
    return np.arccos(np.clip(np.dot(vector1, vector2), -1.0, 1.0))


def find_closest_point_index(point, points):
    """
    Find and return the index of the point closest to the given point from a list of points
    :param point: the point to find the closest to
    :param points: the list of points
    :return: the index of the point closest to the given point
    """
    distances = np.linalg.norm(points - point, axis=1)
    return np.argmin(distances)


def find_closest_point(point, points):
    """
    Find and return the point closest to the given point from a list of points
    :param point: the point to find the closest to
    :param points: the list of points
    :return: the point closest to the given point
    """
    return points[find_closest_point_index(point, points)]


def get_perpendicular_vector(point1, point2, direction=0, normalized=True):
    """
    Returns one of the two perpendicular vectors to the vector between the two given points and optionally normalizes it
    :param point1: the first point
    :param point2: the second point
    :param direction: the direction of the resulting vector (either 0 or 1)
    :param normalized: whether the result should be normalized
    :return: the perpendicular vector to the vector between the two points
    """
    point1 = point1.reshape(2)
    point2 = point2.reshape(2)
    result = np.flip(point2 - point1, axis=0)
    result[direction] = -result[direction]
    return result / fast_norm(result) if normalized else result


def create_line_iterator(point1, point2, img):
    """
    Produces and array that consists of the coordinates and intensities of each pixel in a line between two points
    (see https://stackoverflow.com/a/32857432/868291)
    :param point1: the first point
    :param point2: the second point
    :param img: the image being processed
    :return: a numpy array that consists of the coordinates and an array with the intensities of each pixel in the radii
    (shape: [numPixels, 3], row = [x,y,intensity])
    """
    # Define local variables for readability
    imageH = img.shape[1]
    imageW = img.shape[0]
    P1X = point1[0]
    P1Y = point1[1]
    P2X = point2[0]
    P2Y = point2[1]

    # Difference and absolute difference between points (used to calculate slope and relative location between points)
    dX = P2X - P1X
    dY = P2Y - P1Y
    dXa = np.abs(dX)
    dYa = np.abs(dY)

    # Predefine numpy array for output based on distance between points
    itbuffer = np.empty(shape=(np.maximum(dYa, dXa), 2), dtype=np.float32)
    itbuffer.fill(np.nan)

    # Obtain coordinates along the line using a form of Bresenham's algorithm
    negY = P1Y > P2Y
    negX = P1X > P2X
    if P1X == P2X:  # Vertical line segment
        itbuffer[:, 0] = P1X
        if negY:
            itbuffer[:, 1] = np.arange(P1Y - 1, P1Y - dYa - 1, -1)
        else:
            itbuffer[:, 1] = np.arange(P1Y+1, P1Y+dYa+1)
    elif P1Y == P2Y:  # Horizontal line segment
        itbuffer[:, 1] = P1Y
        if negX:
            itbuffer[:, 0] = np.arange(P1X-1, P1X-dXa-1, -1)
        else:
            itbuffer[:, 0] = np.arange(P1X+1, P1X+dXa+1)
    else:  # Diagonal line segment
        steepSlope = dYa > dXa
        if steepSlope:
            slope = dX.astype(np.float32) / dY.astype(np.float32)
            if negY:
                itbuffer[:, 1] = np.arange(P1Y-1, P1Y-dYa-1, -1)
            else:
                itbuffer[:, 1] = np.arange(P1Y+1, P1Y+dYa+1)
            itbuffer[:, 0] = (slope*(itbuffer[:, 1]-P1Y)).astype(np.int) + P1X
        else:
            slope = dY.astype(np.float32) / dX.astype(np.float32)
            if negX:
                itbuffer[:, 0] = np.arange(P1X-1, P1X-dXa-1, -1)
            else:
                itbuffer[:, 0] = np.arange(P1X+1, P1X+dXa+1)
            itbuffer[:, 1] = (slope*(itbuffer[:, 0]-P1X)).astype(np.int) + P1Y

    # Remove points outside of image
    colX = itbuffer[:, 0]
    colY = itbuffer[:, 1]
    itbuffer = itbuffer[(colX >= 0) & (colY >= 0) & (colX < imageW) & (colY < imageH)]

    # Get intensities from img ndarray
    intensities = img[itbuffer[:, 0].astype(np.uint), itbuffer[:, 1].astype(np.uint)]
    return itbuffer, intensities
