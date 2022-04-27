import os
import sys
import boto3
import tempfile
import datetime
import shutil
import traceback
import tarfile
import zipfile
import pathlib
import configparser
from os import listdir
from os.path import isfile, join

s3 = boto3.client("s3")

config = configparser.ConfigParser()
config.read("example.ini")

output_bucket = config["DEFAULT"]["output_bucket"]

def upload_file(file):
    try:
        key = f"{collection}/{name}"
        s3.upload_file(file, output_bucket, os.path.basename(file))

        print("File uploaded to s3")
        return f"s3://{output_bucket}/{key}"
    except Exception as e:
        print("Failed to copy to S3 bucket")
        print(e)
        return None


def download_file(temp_dir, file_uri):
    filename = f"{temp_dir}/{os.path.basename(file_uri)}"

    path_parts = file_uri.split("://")[1].split("/")
    bucket = path_parts[0]
    path = "/".join(path_parts[1:])
    s3.download_file(bucket, path, filename)

    return filename

def extract(temp_dir, inp):
    if pathlib.Path(inp.get('s3_filename')).suffix == ".gz":
        out_s3 = download_file(temp_dir, inp.get('s3_filename'))

        file = tarfile.open(out_s3)
        file.extractall(f'{temp_dir}/')
        os.remove(out_s3)

        res = []
        for f in listdir(temp_dir):
            if not isfile(join(temp_dir, f)):
                continue

            s3_path = upload_file(join(temp_dir, f))

            res.append({
                "collection": inp.get('collection', 'default'),
                "s3_datetime": inp.get('s3_datetime', datetime.datetime.now().isoformat()),
                "s3_filename": s3_path
            })
    else:
        return None


def handler(event, context):
    temp_dir = tempfile.mkdtemp()

    try:
        for e in event:
            s3_paths = extract(temp_dir, e)

            if s3_paths is not None:
                event['s3_filename'] = s3_path
    except:
        print(traceback.format_exc())

    try:
        shutil.rmtree(temp_dir)
    except:
        print(traceback.format_exc())

    return event


if __name__ == "__main__":
    sample_event = [{
        "s3_filename": "s3://covid-eo-blackmarble/FinalBMHD_DashboardEvolution.tar.gz",
        "collection": "default",
        "s3_datetime": "2022-04-18T20:22:29+00:00"
    }]

    handler(sample_event, {})
