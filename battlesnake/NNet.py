from battlesnake import config
import tensorflow as tf


class NNet(object):
    def __init__(self,
                 shape,
                 scope = config.dir_name,
                 learning_rate = config.learning_rate):

        self.graph = self.__build_model(shape,
                                        learning_rate = learning_rate,
                                        num_channels = num_channels,
                                        action_size = action_size)

        config = tf.ConfigProto(log_device_placement = False)
        config.gpu_options.allocator_type = 'BFC'
        # config.gpu_options.per_process_gpu_memory_fraction = 0.4
        config.gpu_options.allow_growth = True

        self.sess = tf.Session(graph = self.graph, config = config)

        self._saver = tf.train.Saver(tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope = scope))

    def __build_model(self, shape: int, learning_rate: float, num_channels: float, action_size: int):
        pass

    def get_output(self):
        pass
