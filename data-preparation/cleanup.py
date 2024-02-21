import boto3
import yaml
from rich.progress import track

if __name__ == '__main__':
    with open("config.yaml", "r") as stream:
        CONFIG = yaml.safe_load(stream)
        s3 = boto3.resource(
            's3',
            region_name=CONFIG["region_name"],
            aws_secret_access_key=CONFIG["aws_secret_access_key"],
            aws_access_key_id=CONFIG["aws_access_key_id"],
            endpoint_url=CONFIG["endpoint_url"]
        )

        bucket = s3.Bucket(CONFIG['bucket'])
        objects = bucket.objects.all()
        for obj in track(objects, description="Deleting files"):
            obj.delete()
        print("Completed deleting all the files.")