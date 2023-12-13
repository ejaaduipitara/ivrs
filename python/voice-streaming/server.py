from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from pydub import AudioSegment
from pydub.utils import make_chunks

import base64
import json
import math

app = Flask(__name__)
sockets = Sockets(app)
connection_chunks = json.loads('{}')
duration = 20 # no of milliseconds of each base64 string from audio file

def convert_to_base64(session_id, file_path):
    audio = AudioSegment.from_wav(file_path)

    # Define the number of parts you want to split the audio into
    total_length = len(audio)
    num_parts = math.ceil(total_length / (duration * 1000))

    chunks = []
    raw_chunks = make_chunks(audio, duration)

    for i, chunk in enumerate(raw_chunks):
        start = i * duration
        end = (i + 1) * duration

        try:
            chunks.append({
                "event": "media",
                "stream_sid": session_id,
                "sequence_number": str(i + 1),
                "media": {
                    "chunk": str(i + 1),
                    "timestamp": str(int(start)),
                    "payload": base64.b64encode(chunk.raw_data).decode("utf-8")
                }
            })
        except:
            print('An exception occurred')

    return chunks

@sockets.route('/media')
def echo(ws):
    while not ws.closed:
        # print(ws.receive())
        message = ws.receive()
        # print(message)
        if message is None:
            continue
        request_payload = json.loads(message)
        event = request_payload['event']
        if event == "media":
            # chunk = get_payload(request)
            pass
        elif event == 'dtmf':
            print("inside dtmf")
            chunks_events = convert_to_base64(request_payload['stream_sid'], "StarWars60.wav")
            # print(chunks_events)
            
            for chunk in chunks_events:
                chunk_str = json.dumps(chunk)
                print(chunk_str)
                ws.send(chunk_str)
            
            mark_event = {"event":"mark","sequence_number": int(request_payload['sequence_number']) + 1,"stream_sid":request_payload['stream_sid'],"mark":{"name":"reply complete"}}
            # ws.send(json.dumps(mark_event))
        elif event == "stop":
            print("inside stop")

HTTP_SERVER_PORT = 8000
server = pywsgi.WSGIServer(('localhost', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)

print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
print("Route for media: http://localhost:" + str(HTTP_SERVER_PORT) + '/media')

server.serve_forever()

def get_payload(request):
    payload = request['media']['payload']
    chunk = base64.b64decode(payload)
    return chunk