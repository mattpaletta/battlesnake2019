import logging

import tensorflow as tf

import os
from copy import deepcopy
import random
import math

from battlesnake import config
from battlesnake.state import State
from battlesnake.trainer import Trainer
from battlesnake.NNet import NNet

import numpy as np



class Move(object):
    up    = (0, -1)
    down  = (0,  1)
    left  = (-1, 0)
    right = ( 1, 0)


ORIENTATION = {(0, -1): 'up', (0, 1): 'down', (-1, 0): 'left', (1, 0): 'right'}
ORIENTATION_ADJUSTER = {'up': {0: Move.up, 1: Move.down, 2: Move.left, 3: Move.right},
                        'down': {0: Move.down, 1: Move.up, 2: Move.right, 3: Move.left},
                        'left': {0: Move.left, 1: Move.right, 2: Move.down, 3: Move.up},
                        'right': {0: Move.right, 1: Move.left, 2: Move.up, 3:Move.down}}


def manhattan_distance(head, other_snake):
    # Subtract the x and y coordinates and add them together to get the distance from head to other_snake
    return abs(head[0] - other_snake[0]) + abs(head[1] - other_snake[1])


class Snake(object):
    def __init__(self):
        # Game specific parameters
        self.strategy = lambda s_id, state : self.get_action(s_id, state)

        self._sight_distance = config.sight_distance
        vision_grid_size = int(math.ceil(math.pow(self._sight_distance*2 + 1, 2) / 2))
        self._num_inputs = 6 * vision_grid_size + 103

        sess = tf.Session()
        self._network = NNet(shape = [self._num_inputs, config.num_nodes, len(ORIENTATION.keys())])

        self._radars_index = {
            'self'                 : 0,
            'vulnerable-enemy-head': 1 * vision_grid_size,
            'dangerous-enemy-head' : 2 * vision_grid_size,
            'enemy-tail'           : 3 * vision_grid_size,
            'food'                 : 4 * vision_grid_size,
            'wall'                 : 5 * vision_grid_size,
            'health'               : 6 * vision_grid_size,
            'food-ratio'           : -2
        }

        self._displacement = {}
        i = 0
        for x in range(-self._sight_distance, self._sight_distance + 1):
            for y in range(-self._sight_distance, self._sight_distance + 1):
                if manhattan_distance([0, 0], [x, y]) <= self._sight_distance:
                    self._displacement[(x, y)] = i
                    i += 1

    def get_action(self, state: State, reward=0):
        self.snake_id = state.self_id

        is_done = (reward != 0)
        logging.debug('Reward: {0}\n'.format(reward))

        if state.is_new_game():
            self.get_overriden_action(state)

        self._orientation = self._get_orientation(state)
        self._radars = np.zeros(self._num_inputs)
        self._state = np.reshape(self._radars, (-1, self._num_inputs))

        self._populate_features(state)

        a = self._network.get_output(self._state)

        print(ORIENTATION[ORIENTATION_ADJUSTER[self._orientation][int(a)]])

        if hasattr(self, '_previous_state') and config.is_training:
            self.log_statistics(reward, is_done)
            self._trainer.train_network(self._previous_state, self._previous_action, reward, self._state, is_done)

            self._network.save_network()

        self._previous_state = self._state
        self._previous_action = a

        return ORIENTATION[ORIENTATION_ADJUSTER[self._orientation][int(a)]]

    def get_overriden_action(self, state):
        x, y = state.get_self_snake_coords()

        if x == 0:
            return 'right'
        elif x == state.grid_size[0] - 1:
            return 'left'
        elif y == 0:
            return 'down'
        elif y == state.grid_size[1] - 1:
            return 'up'

    def _get_orientation(self, state):
        snakes = state.snakes
        for (snake_id, snake_pos) in snakes.iteritems():
            if snake_id == self.snake_id:
                return ORIENTATION[(snake_pos[0][0] - snake_pos[1][0], snake_pos[0][1] - snake_pos[1][1])]

    def _populate_features(self, state):
        snakes = state.snakes
        grid_size = state.grid_size
        health = state.self_health

        for (snake_id, snake_pos) in snakes.iteritems():
            if snake_id == self.snake_id:
                self_head = snake_pos[0]
                self_size = len(snake_pos)

        # Add self
        for (snake_id, snake_pos) in snakes.iteritems():
            if snake_id == self.snake_id:
                for snake_cell in snake_pos:
                    if manhattan_distance(self_head, snake_cell) <= self._sight_distance:
                        self._add_to_self_grid(self_head, snake_cell, 'self')

        # Add vulnerable enemy snakes' heads
        for (snake_id, snake_pos) in snakes.iteritems():
            if snake_id != self.snake_id and self_size > len(snake_pos):
                if manhattan_distance(self_head, snake_pos[0]) <= self._sight_distance:
                    self._add_to_self_grid(self_head, snake_pos[0], 'vulnerable-enemy-head')

        # Add dangerous enemy snakes' heads
        for (snake_id, snake_pos) in snakes.iteritems():
            if snake_id != self.snake_id and self_size <= len(snake_pos):
                if manhattan_distance(self_head, snake_pos[0]) <= self._sight_distance:
                    self._add_to_self_grid(self_head, snake_pos[0], 'dangerous-enemy-head')

        # Add enemy snakes' tails
        for (snake_id, snake_pos) in snakes.iteritems():
            if snake_id != self.snake_id:
                for snake_cell in snake_pos:
                    if manhattan_distance(self_head, snake_cell) <= self._sight_distance and snake_cell != snake_pos[0]:
                        self._add_to_self_grid(self_head, snake_cell, 'enemy-tail')

        # Add food
        for position in state.food:
            if manhattan_distance(self_head, position) <= self._sight_distance:
                self._add_to_self_grid(self_head, position, 'food')

        # Add upper wall
        for i in range(0, grid_size[0] + 1):
            cell = [i, -1]
            if manhattan_distance(self_head, cell) <= self._sight_distance:
                self._add_to_self_grid(self_head, cell, 'wall')

        # Add right wall
        for i in range(0, grid_size[1] + 1):
            cell = [grid_size[0], i]
            if manhattan_distance(self_head, cell) <= self._sight_distance:
                self._add_to_self_grid(self_head, cell, 'wall')

        # Add down wall
        for i in range(0, grid_size[0] + 1):
            cell = [i, grid_size[1]]
            if manhattan_distance(self_head, cell) <= self._sight_distance:
                self._add_to_self_grid(self_head, cell, 'wall')

        # Add left wall
        for i in range(0, grid_size[1] + 1):
            cell = [-1, i]
            if manhattan_distance(self_head, cell) <= self._sight_distance:
                self._add_to_self_grid(self_head, cell, 'wall')

        # Add health
        self._radars[self._radars_index['health'] + health] = 1
        self._radars[self._radars_index['food-ratio'] + (0 if len(snakes) / float(len(state.food)) <= 1 else 1)] = 1

    def _add_to_self_grid(self, self_head, cell_to_modify, radar_to_modify):
        # Get distance relative to head of snake
        x_distance = (cell_to_modify[0] - self_head[0])
        y_distance = (cell_to_modify[1] - self_head[1])
        cell_from_head = self._rotate((x_distance, y_distance))

        self._radars[self._radars_index[radar_to_modify] + self._displacement[cell_from_head]] = 1

    def _rotate(self, cell):
        if self._orientation == 'up':
            return cell
        elif self._orientation == 'right':
            return (cell[1], -cell[0])
        elif self._orientation == 'left':
            return (-cell[1], cell[0])
        else:
            return (-cell[0], -cell[1])

    def log_statistics(self, reward, is_done):
        if is_done:
            self._episode_count += 1
            self.episode_rewards.append(reward)

            # Statistics
            mean_reward = np.mean(self.episode_rewards[-5:])

            summary = tf.Summary()
            summary.value.add(tag='Performance/Reward', simple_value=float(mean_reward))
            self._summary_writer.add_summary(summary, self._episode_count)

            self._summary_writer.flush()
