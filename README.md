# MyJP IVRS Bot

## Steps to prerequisites:

### Step 1
Install python 3.11

### Step 2
Install dependency libraries with below command
```
pip install -r requirements.txt
```

## Steps To Upload audio files to cloud

### Step 1

Get the audio files and place the audio files in the `drive-files` folder

### Step 2

Update the config file `config.yaml` with cloud storage credentials in below format

```
region_name: ""
aws_secret_access_key: ""
aws_access_key_id: ""
endpoint_url: ""

```

### Step 3

Create the csv file in below format.
```
filename,category,language
"32-Track 1 Bangla PoemPoem Rhymes for eJadui Pitara.mp3",song,bengali
"33-Track 2 Bangla Poem Rhymes for eJadui Pitara.mp3",song,bengali
```

### Step 4

Run the below command to upload the audio files and update the ivrs_config.json file

```
python generate-config.py csv_file_name

# Example
python generate-config.py audios.csv
```
