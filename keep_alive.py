from flask import Flask
from threading import Thread

app = Flask('')

app.config.update(
    DEBUG=False,
    TESTING=False
)

@app.route('/')
def home():
    return """
    <head><link rel="shortcut icon" href="#"></head>
    <img src=https://cdn.discordapp.com/attachments/660285290404904982/970615387341357056/unknown.png>
    """

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()