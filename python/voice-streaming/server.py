from flask import Flask
from flask_sockets import Sockets

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import base64
import json

app = Flask(__name__)
sockets = Sockets(app)
connection_chunks = json.loads('{}')

@sockets.route('/media')
def echo(ws):
    while not ws.closed:
        message = ws.receive()
        if message is None:
            continue
        
        request = json.loads(message)
        event = request['event']
        if event == "media":
            chunk = get_payload(request)
            



HTTP_SERVER_PORT = 8000
server = pywsgi.WSGIServer(('localhost', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)

print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
print("Route for media: http://localhost:" + str(HTTP_SERVER_PORT) + '/media')

server.serve_forever()


def get_payload(request):
    payload = request['media']['payload']
    chunk = base64.b64decode(payload)
    return chunk