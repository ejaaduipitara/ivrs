import json
import base64
from six.moves import queue
import wave


# SLIN16 audio parameters
sample_width = 2  # 16 bits per sample
channels = 1  # Mono audio
frame_rate = 8000  # Sample rate (adjust as needed)

def read_request_file(file_path):
    file = open(file_path, 'r')
    lines = file.readlines()
    chunks = []
    for line in lines:
        request = json.loads(line)
        event = request['event']
        if event == "media":
            payload = request['media']['payload']
            chunk = base64.b64decode(payload)
            chunks.append(chunk)
    return chunks

def write_audio_file(chunks, audio_file_path):
    wav_file = wave.open(audio_file_path, 'w')
    wav_file.setnchannels(channels)
    wav_file.setsampwidth(sample_width)
    wav_file.setframerate(frame_rate)
    for chunk in chunks:
        wav_file.writeframesraw(chunk)


if __name__ == '__main__':
    file_path = 'all-requests-updated.log'
    output_wav_file = 'output.wav'
    chunks = read_request_file(file_path)
    write_audio_file(chunks=chunks, audio_file_path=output_wav_file)
    
    
    
        
        
