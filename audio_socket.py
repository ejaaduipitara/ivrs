from pydub import AudioSegment
from pydub.utils import make_chunks
from flask import Blueprint
from datetime import datetime
from urllib.parse import parse_qs
from telemetry import Telemetry

import os
import json
import base64
import subprocess

from urllib import request as downloader
from pathlib import Path

audio_socket = Blueprint('audio_socket', __name__)
duration = 20 # no of milliseconds of each base64 string from audio file
audio_types = ["story", "rhyme", "riddle"]

AUDIO_CACHE = {}

def get_audio(input_selector, language):

    if input_selector > 2:
        return None

    urlData = os.environ['IVRS_CONFIG_URL']
    webURL = downloader.urlopen(urlData)
    data = webURL.read()
    encoding = webURL.info().get_content_charset('utf-8')
    config = json.loads(data.decode(encoding))

    audio_type = audio_types[input_selector]
    no_of_audios = len(config[f"{audio_type}:{language}"])

    day_of_year = datetime.today().timetuple().tm_yday
    mod_day_no = int(day_of_year % no_of_audios)

    audio_index = no_of_audios if mod_day_no == 0 else mod_day_no

    return config[f"{audio_type}:{language}"][audio_index - 1]

def get_chunks(input_selector, language, file_path):
    audio_type = audio_types[input_selector]

    day_of_year = datetime.today().timetuple().tm_yday
    path = Path(file_path)
    filename = path.stem + path.suffix.split("?")[0]

    cache_key = f"{audio_type}:{language}"

    if cache_key in AUDIO_CACHE:
        chunk_detail = AUDIO_CACHE[cache_key]

        if chunk_detail['cached_on'] == day_of_year:
            return chunk_detail['chunks']

    path = Path(file_path)
    filename = path.stem + path.suffix.split("?")[0]
    local_file_path = "temp_audio_files/" + filename
    local_converted_file_path = "temp_converted_files/" + path.stem + ".wav"

    downloader.urlretrieve(file_path, local_file_path)

    subprocess.call(['ffmpeg', '-i', local_file_path, '-ar', '8000', '-ab', '128', '-ac', '1', '-y', local_converted_file_path])

    audio = AudioSegment.from_file(local_converted_file_path)

    # Define the number of parts you want to split the audio into
    raw_chunks = make_chunks(audio, duration)
    chunks_array = []
    for i, chunk in enumerate(raw_chunks):
        start_time = i * duration

        chunks_array.append({
            "event": "media",
            "sequence_number": str(i + 1),
            "media": {
                "chunk": str(i + 1),
                "timestamp": str(int(start_time)),
                "payload": base64.b64encode(chunk.raw_data).decode("utf-8")
            }
        })

    AUDIO_CACHE[cache_key] = {'cached_on': day_of_year, 'chunks': chunks_array}

    remove_temp_file(local_file_path)
    remove_temp_file(local_converted_file_path)

    return chunks_array

def remove_temp_file(file_path):
    os.remove(file_path)

@audio_socket.route('/media')
def echo(ws):
    language = ''
    telemetry = None
    while not ws.closed:
        message = ws.receive()
        # print(message)
        if message is None:
            continue
        request_payload = json.loads(message)
        event = request_payload['event']

        if event == 'start':
            telemetry = Telemetry(request_payload['stream_sid'])
            telemetry.start()
        elif event == "media":
            # chunk = get_payload(request)
            pass
        elif event == 'dtmf':
            url_params = parse_qs(ws.environ['QUERY_STRING'])
            if "language" in url_params:
                language = url_params["language"][0].lower()
            else:
                continue

            session_id = request_payload['stream_sid']
            print("inside dtmf")
            # clear the existing audio events if it's playing already
            mark_event = {"event":"clear","stream_sid":session_id}
            ws.send(json.dumps(mark_event))

            input_selector = int(request_payload["dtmf"]["digit"]) - 1

            audio_url = get_audio(input_selector, language)
            selected_audio_type = audio_types[input_selector] if input_selector < len(audio_types) else None
            telemetry.interact(input=input_selector, language=language, audio_type=selected_audio_type,audio_name=audio_url)
            if audio_url:
                chunks = get_chunks(input_selector, language, audio_url)
                for chunk in chunks:
                    chunk["stream_sid"] = session_id
                    ws.send(json.dumps(chunk))
            else:
                pass

            # mark_event = {"event":"mark","sequence_number": int(request_payload['sequence_number']) + 1,"stream_sid":request_payload['stream_sid'],"mark":{"name":"reply complete"}}
            # ws.send(json.dumps(mark_event))
        elif event == "stop":
            telemetry.end()
            telemetry.push()
            print("inside stop")
