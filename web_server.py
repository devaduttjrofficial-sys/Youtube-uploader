from flask import Flask
import threading
import config
import logging

app = Flask(__name__)

# Reduce flask logging unless DEBUG is on
log = logging.getLogger('werkzeug')
if not config.DEBUG:
    log.setLevel(logging.ERROR)


@app.route('/')
def health_check():
    return "Bot is running", 200


def run_server():
    app.run(host="0.0.0.0", port=config.PORT)


def keep_alive():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    return t
