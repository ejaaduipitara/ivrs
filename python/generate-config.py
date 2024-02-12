import sys
import csv
import re
import json
# import gdown
import boto3
import yaml


from pathlib import Path

CONFIG = {}

def get_upload_path(file_name, category, language):
    if category != "" and language != "": 
        return f'audio/{category}/{language}/{file_name}'
    else:
        return f'audio/{file_name}'

def upload_to_oci_storage(s3, file_name, category, language):
    try:
        file_path = Path(file_name)
        upload_path = get_upload_path(file_path.name, category, language)
        s3.meta.client.upload_file(f"drive-files/{file_name}", CONFIG['bucket'], upload_path)
        print(upload_path, "uploaded successfully")
    except Exception as e:
        print(e)

def create_config(s3):
    config = {}
    categories = set()
    languages = set()

    invalid_option_link = ["https://objectstorage.ap-hyderabad-1.oraclecloud.com/n/ax2cel5zyviy/b/sbdjp-ivrs/o/audio/invalid_option_english.mp3"]

    for obj in s3.Bucket(CONFIG['bucket']).objects.all():
        path = Path(obj.key)
        
        if len(path.parts) < 4: continue
        
        if path.parts[0] != "audio": continue
        
        category = path.parts[1].strip().lower()
        language = path.parts[2].strip().lower()
        
        categories.add(category)
        languages.add(language)
        audio_key = f"{category}:{language}"
        if audio_key not in config: config[audio_key] = []
        
        url = s3.meta.client.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': CONFIG['bucket'], 'Key': obj.key })
        url = url.split("?")[0]

        config[audio_key].append(url)
        
    for lang in languages:
        for cat in categories:
            audio_key = f"{cat}:{lang}:empty"
            config[audio_key] = invalid_option_link
        
        audio_key = f"invalid_option:{lang}"
        config[audio_key] = invalid_option_link
        
    with open('drive-files/ivrs_config.json', 'w') as f:
        f.write(json.dumps(config))

if __name__ == '__main__':
    n = len(sys.argv)
    if n < 1:
        print('Usage: generate-config.py <csv file>')
        exit(1)

    with open("config.yaml", "r") as stream:
        CONFIG = yaml.safe_load(stream)
        s3 = boto3.resource(
            's3',
            region_name=CONFIG["region_name"],
            aws_secret_access_key=CONFIG["aws_secret_access_key"],
            aws_access_key_id=CONFIG["aws_access_key_id"],
            endpoint_url=CONFIG["endpoint_url"]
        )

    with open(sys.argv[1]) as csv_file:
        files_list = [d for d in csv.DictReader(csv_file)]

        for file in files_list:
            category = file["category"].strip().lower()
            language = file["language"].strip().lower()
            try:
                upload_to_oci_storage(s3, file["filename"], category, language)
            except Exception as inst:
                print(inst)

    create_config(s3)
    upload_to_oci_storage(s3, "ivrs_config.json", "", "")

