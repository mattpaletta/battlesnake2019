import functools
import logging
from multiprocessing.pool import Pool
from os import cpu_count

from battlesnake.game import Game
from battlesnake.snake import Snake


class Trainer(object):
    def __init__(self, nnet: Snake, pnet: Snake, game: Game, num_iters: int, board_size: int,
                 max_cpus = cpu_count()):
        self._nnet = nnet
        self._pnet = pnet
        self._num_iters = num_iters
        self._board_size = board_size
        self._max_cpus = max_cpus
        self._game = game

    def learn(self):
        logging.info("Starting learning loop, using {0} cores.".format(self._max_cpus))
        training_examples_history = []
        pool = Pool(processes = self._max_cpus)

        for _ in range(self._num_iters):
            def self_play(s1: Snake):
                pass

            iteration_train_examples = pool.map(functools.partial(self_play, self.game, ))

    def execute_move(self):
