import os
import csv
import re
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydub import AudioSegment
import boto3
import yaml
from rich.progress import track
from collections import defaultdict
import shutil

def download_file(drive, file_id, destination_path, language, category):
    # Get the file
    file = drive.CreateFile({'id': file_id})
    file_name = f"{file['title']}"
    # Download the file
    file_destination_path = f"{destination_path}/{language}/{category}"
    os.makedirs(file_destination_path, exist_ok=True)
    final_file_path = f"{file_destination_path}/{file['title']}"
    file.GetContentFile(final_file_path)
    # print('Downloaded', file_name)
    return final_file_path

def get_drive():
    # Authenticate and create the PyDrive client
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.
    drive = GoogleDrive(gauth)
    return drive

def check_file_existence(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("The file '{}' does not exist.".format(file_path))
    else:
        print("The file given is ".format(file_path))


def download_audio_files(source_file_path):
    downloaded_files = {}
    # Open the CSV file
    with open(source_file_path, encoding="utf8") as csvfile:
        files_list = [d for d in csv.DictReader(csvfile)]
        drive = get_drive()
        # for file in files_list:
        for file in track(files_list, description="Downloading files"):
            category = file["Category"].strip().lower()
            language = file["Language"].strip().lower()
            drive_link = file["Drive Link"]
            file_id = re.search(r'/file/d/([^/]+)/', drive_link).group(1)
            local_file_path = download_file(drive, file_id, destination_path, language, category)
            file["Downloaded Path"] = local_file_path
            if local_file_path not in downloaded_files:
                downloaded_files.setdefault(local_file_path, 1)
            else:
                print(f"File already downloaded: {local_file_path}")
        
        with open("out.csv", "w") as f:
            wr = csv.DictWriter(f, delimiter=",",fieldnames=list(files_list[0].keys()))
            wr.writeheader()
            wr.writerows(files_list)

def get_s3_object_and_bucket():
    with open("config.yaml", "r", encoding="utf8") as stream:
        CONFIG = yaml.safe_load(stream)
        s3 = boto3.resource(
            's3',
            region_name=CONFIG["region_name"],
            aws_secret_access_key=CONFIG["aws_secret_access_key"],
            aws_access_key_id=CONFIG["aws_access_key_id"],
            endpoint_url=CONFIG["endpoint_url"]
        )
        return s3, CONFIG['bucket']

def is_audio_file(file_path):
    _, extension = os.path.splitext(file_path)
    return extension.lower() == '.mp3' or extension.lower() == '.wav'
def list_files(directory):
    # List to store all files
    all_files = []

    # Walk through all directories and subdirectories recursively
    for root, directories, files in os.walk(directory):
        for filename in files:
            # Append the full path to the list
            full_file_path = os.path.join(root, filename)
            if is_audio_file(full_file_path) == True:
                all_files.append(full_file_path)
    return all_files

def change_extension(file_path):
    # Split the file path into directory, base filename, and extension
    directory, filename = os.path.split(file_path)
    base_name, old_extension = os.path.splitext(filename)
    # Construct the new file path with .wav extension
    return os.path.join(directory, base_name + ".wav")

def convert_to_16bit_mono_8k_pcm_wav(mp3_file, wav_file):
    # Load the MP3 file
    audio = AudioSegment.from_mp3(mp3_file)
    # Set channels to mono
    audio = audio.set_channels(1)
    # Set sample width to 2 bytes (16 bit)
    audio = audio.set_sample_width(2)
    # Set sample rate to 8000 Hz
    audio = audio.set_frame_rate(8000)
    # Export as WAV
    audio.export(wav_file, format="wav", bitrate='8k', parameters=["-ac", "1", "-ar", "8000", "-sample_fmt", "s16"])

def convert_and_upload(s3, base_folder, bucket_name):
    file_list = list_files(base_folder)
    # for mp3_file_path in file_list:
    for mp3_file_path in track(file_list, description="Convert & Uploading"):
        # print(f"Processing {mp3_file_path}")
        converted_wav_file_path = change_extension('converted-drive-files/audio/'+'/'.join(mp3_file_path.split('/')[1:]))
        # print(f"Converting to {converted_wav_file_path}")
        try:
            os.makedirs(os.path.dirname(converted_wav_file_path), exist_ok=True)
            # convert_to_8khz_mono_with_bitrate(mp3_file_path, converted_mp3_file_path)
            convert_to_16bit_mono_8k_pcm_wav(mp3_file_path, converted_wav_file_path)
            # print(f"Converted to {converted_wav_file_path}")
            s3_file_path='/'.join(converted_wav_file_path.split('/')[1:])
            s3.meta.client.upload_file(converted_wav_file_path, bucket_name, s3_file_path, ExtraArgs={'ContentType': 'audio/wav'})
            # print(f"Uploaded to {s3_file_path}")
        except Exception as e:
            print("Failed to process and upload ", mp3_file_path)
            pass

def copy_invalid_option_audio(s3, bucket): 
    source_file = 'invalid_option_english.wav'
    # Specify the path to the folder where you want to move the file
    s3.meta.client.upload_file(source_file, bucket, f"audio/{source_file}", ExtraArgs={'ContentType': 'audio/wav'})

if __name__ == "__main__":
    destination_path="original-drive-files"
    source_file_path = input("Please enter input file path: ")
    check_file_existence(source_file_path)
    download_audio_files(source_file_path)
    print("Completed downloading all the files.")
    s3, bucket = get_s3_object_and_bucket()
    convert_and_upload(s3,destination_path,bucket)
    print("Completed uploading all the files.")
    copy_invalid_option_audio(s3, bucket)
    print("Completed copying invalid option audio.")
