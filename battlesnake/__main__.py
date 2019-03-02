import json
from random import randint

import tensorflow as tf
from flask import Flask, request

app = Flask(__name__)

@app.route('/ping')
def ping():
    return "Hello!"

@app.route('/start')
def start():
    return json.dumps({
                "color": "#00FF00"
        })

@app.route('/move', methods=["POST"])
def move():
    move = ['up', 'down', 'left', 'right']

    print(request.data)

    return json.dumps({
            # Start by picking a random move
            "move": move[randint(len(move))]
    })


app.run()
