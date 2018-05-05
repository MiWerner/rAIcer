import numpy as np


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
        if np.array_equal(array[i][0], element):
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
    return np.flip(result, 0) if flip else result


def angle_between_vectors(vector1, vector2):
    """
    Calculates the angle in radians between two vectors by taking the dot product of their unit vectors
    :param vector1: the first vector
    :param vector2: the second vector
    :return: the angle in radians between both vectors
    """
    vector1 = vector1 / np.linalg.norm(vector1)
    vector2 = vector2 / np.linalg.norm(vector2)
    return np.arccos(np.clip(np.dot(vector1, vector2), -1.0, 1.0))

