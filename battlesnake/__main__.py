import json
from random import randint
from flask import Flask, request

app = Flask(__name__)


@app.route('/ping', methods=["POST"])
def ping():
    return "Hello!"


@app.route('/start', methods=["POST"])
def start():
    return json.dumps({
        "color": "#00FF00"
    })


@app.route('/move', methods=["POST"])
def move():
    move = ['up', 'down', 'left', 'right']

    print(request.data)

    board = request.data["board"]
    snakes = request.data["snakes"]
    you = request.data["snakes"]["you"]
    game_id = request.data["game"]["id"]
    game_turn = request.data["game"]["turn"]

    return json.dumps({
        # Start by picking a random move
        "move": move[randint(a = 0, b = len(move) - 1)]
    })


app.run()
