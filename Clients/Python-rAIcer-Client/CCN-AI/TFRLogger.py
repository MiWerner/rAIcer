"""
Contains methods to save and read data in tf-record files. Those are optimised for tensorflow.
"""
import tensorflow as tf
from Utils import IMG_HEIGHT, IMG_WIDTH


def _int64_feature(value):
    """
    Converts the parameter value of type integer
    :param value: the data
    :return: a tfrecord feature
    """
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def _bytes_feature(value):
    """
    Converts the parameter value of type byte
    :param value: the data
    :return: a tfr feature
    """
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def create_tfrecord_writer(filename):
    """
    Creates
    :param filename:
    :return:
    """
    return tf.python_io.TFRecordWriter(filename)


def close_tfrecord_writer(writer):
    """
    Closes the given writer
    :param writer: the writer that has to be closed
    :return:
    """
    writer.close()


def save_data(tfrecord_writer, b_image, keys):
    """
    saves the given image and keys-states in to the given file. The file has to a tfrecord file.
    :param tfrecord_writer: writer for the aimed tfrecord-file
    :param b_image: the image that has to be saved in binary
    :param keys: the state of the keys Up, Down, Left, Right. Assert integer values [0, 1]
    :return:
    """
    print("keys:")
    print(keys)
    feature = {
        'image': _bytes_feature(b_image),
        'keys': _int64_feature(keys)
    }
    example = tf.train.Example(features=tf.train.Features(feature=feature))
    tfrecord_writer.write(example.SerializeToString())


def read_data(filename_queue):
    """
    Creates a TFRRecordReader and extents the graph for reading from the files in filename_queue
    The images will be reshaped into [IMAGE_HEIGHT, IMAGE_WIDTH, 3].
    :param filename_queue: queue of tfrecord files
    :return:
    """
    feature = {
        'image': tf.FixedLenFeature([], tf.string),
        'keys': tf.FixedLenFeature([], tf.int64)
    }

    # create reader and read next record
    reader = tf.TFRecordReader()
    key, record_string = reader.read(filename_queue)

    # decode the record
    features = tf.parse_single_example(record_string, features=feature)

    # convert data
    image = tf.decode_raw(features['image'], tf.int64)
    image = tf.reshape(image, [IMG_HEIGHT, IMG_WIDTH, 3])
    keys = tf.cast(features['keys'], tf.int32)

    return image, keys


def input_pipeline(filenames, num_read_threads, num_epochs, batch_size):
    """
    Creates a input pipeline reading from the files in filenames
    :param filenames: list of filenames
    :param num_read_threads: number of threads used to read the files
    :param num_epochs: number of epochs or how often the files have to be read
    :param batch_size: the size of requested batches
    :return: image_batch: tensor for the image of a batch
             keys_batch: tensor for the keys of a batch
    """
    filename_queue = tf.train.string_input_producer(string_tensor=filenames,
                                                    num_epochs=num_epochs,
                                                    shuffle=True)
    example_list = [read_data(filename_queue=filename_queue) for _ in range(num_read_threads)]
    min_after_dequeue = 10000
    capacity = min_after_dequeue + 3 * batch_size
    image_batch, keys_batch = tf.train.shuffle_batch_join(tensors_list=example_list,
                                                          batch_size=batch_size,
                                                          capacity=capacity,
                                                          min_after_dequeue=min_after_dequeue,
                                                          enqueue_many=False,
                                                          shapes=None,
                                                          allow_smaller_final_batch=True,
                                                          shared_name=None,
                                                          name='sample_to_shuffled_batches')
    return image_batch, keys_batch
