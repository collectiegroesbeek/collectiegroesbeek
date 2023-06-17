import subprocess
import threading
import time
from datetime import datetime

import flask

from .. import app


DROPBOX_TIMESTAMP_LOCK = threading.Lock()


@app.route('/api/dropbox-webhook/', methods=['GET'])
def dropbox_webhook_verification():
    resp = flask.Response(flask.request.args.get('challenge'))
    resp.headers['Content-Type'] = 'text/plain'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp


@app.route('/api/dropbox-webhook/', methods=['POST'])
def dropbox_webhook():
    timestamp = int(time.time())
    with DROPBOX_TIMESTAMP_LOCK:
        with open("webhook_timestamp.txt") as f:
            timestamp_last_incoming_webhook = int(f.read())
        with open("webhook_timestamp.txt", "w") as f:
            f.write(str(timestamp))
    if (timestamp - timestamp_last_incoming_webhook) > 300:
        with open("/var/log/dropbox.log", "a") as f_log:
            f_log.write(f'\n{datetime.now()} incoming webhook\n')
            subprocess.Popen(
                ['./run_import.sh'],
                stdout=f_log,
                stderr=f_log,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )
    return flask.make_response("", 200)
