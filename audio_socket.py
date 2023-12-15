from pydub import AudioSegment
from pydub.utils import make_chunks
from flask import Blueprint

import os
import json
import base64
import subprocess
from urllib import request as downloader
from pathlib import Path

audio_socket = Blueprint('audio_socket', __name__)
duration = 20 # no of milliseconds of each base64 string from audio file

def send_audio(session_id, file_path, ws):
    path = Path(file_path)
    local_file_path = "temp_audio_files/" + path.name
    local_converted_file_path = "temp_converted_files/" + path.stem + ".wav"
    
    downloader.urlretrieve(file_path, local_file_path)

    subprocess.call(['ffmpeg', '-i', local_file_path, '-ar', '8000', '-ab', '128', local_converted_file_path])

    audio = AudioSegment.from_file(local_converted_file_path)

    # Define the number of parts you want to split the audio into
    raw_chunks = make_chunks(audio, duration)

    for i, chunk in enumerate(raw_chunks):
        start_time = i * duration

        chunk_str = json.dumps({
            "event": "media",
            "stream_sid": session_id,
            "sequence_number": str(i + 1),
            "media": {
                "chunk": str(i + 1),
                "timestamp": str(int(start_time)),
                "payload": base64.b64encode(chunk.raw_data).decode("utf-8")
            }
        })
        ws.send(chunk_str)

    remove_temp_file(local_converted_file_path)
    remove_temp_file(local_file_path)
        
def remove_temp_file(file_path):
    os.remove(file_path)

@audio_socket.route('/media')
def echo(ws):
    while not ws.closed:
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
            send_audio(request_payload['stream_sid'], "https://storage.googleapis.com/jugalbandi-poc/generic_qa/output_audio_files/audio-output-20231213-092540.mp3", ws)
            
            mark_event = {"event":"mark","sequence_number": int(request_payload['sequence_number']) + 1,"stream_sid":request_payload['stream_sid'],"mark":{"name":"reply complete"}}
            # ws.send(json.dumps(mark_event))
        elif event == "stop":
            print("inside stop")
