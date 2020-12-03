import json
import logging
from random import randint
from flask import Flask, request
from pynotstdlib.logging import default_logging

from battlesnake.NNet import NNet
from battlesnake.snake import Snake
from battlesnake.state import State
from battlesnake.trainer import Trainer


default_logging(logging.INFO)
app = Flask(__name__)

@app.route('/ping', methods=["POST"])
def ping():
    return "Hello!"


@app.route('/start', methods=["POST"])
def start():
    return json.dumps({
        "color": "#00FF00"
    })


snake = Snake()


@app.route('/move', methods=["POST"])
def move():
    move = ['up', 'down', 'left', 'right']

    import pprint
    pp = pprint.PrettyPrinter(indent = 4)
    print(pp.pformat(request.json))
    state = State(world = request.json)

    snake.get_action(state)

    return json.dumps({
        # Start by picking a random move
        "move": move[randint(a = 0, b = len(move) - 1)]
    })


if __name__ == "__main__":
    setting = "train"

    if setting == "train":
        nnet = NNet()
        pnet = NNet()
        trainer = Trainer(nnet = nnet, pnet = pnet)


    app.run()
