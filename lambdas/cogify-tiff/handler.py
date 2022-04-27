from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rasterio.io import MemoryFile
import os
import sys
import requests
import boto3
import configparser
import tempfile
import shutil
import traceback

config = configparser.ConfigParser()
config.read("example.ini")
s3 = boto3.client("s3")

# Set COG inputs
output_bucket = config["DEFAULT"]["output_bucket"]
output_dir = config["DEFAULT"]["output_dir"]
collection = config["DEFAULT"]["collection"]

def upload_file(mem_file, name):
    try:
        key = f"{collection}/{name}"
        s3.upload_fileobj(mem_file, output_bucket, key)

        print("File uploaded to s3")
        return f"s3://{output_bucket}/{key}"
    except Exception as e:
        print("Failed to copy to S3 bucket")
        print(e)
        return None


def download_file(temp_dir, file_uri: str):
    filename = f"{temp_dir}/{os.path.basename(file_uri)}"
    if "http" in file_uri:
        with requests.Session() as session:
            request = session.request("get", file_uri)
            response = session.get(request.url)
            print("RESPONSE IS")
            print(response.status_code)
            with open(filename, "wb") as f:
                f.write(response.content)
    elif "s3://" in file_uri:
        path_parts = file_uri.split("://")[1].split("/")
        bucket = path_parts[0]
        path = "/".join(path_parts[1:])
        s3.download_file(bucket, path, filename)
    else:
        print(f"{filename} file already downloaded")

    return filename


def to_cog(input, upload=None):
    """Convert image to COG."""
    # Format creation option (see gdalwarp `-co` option)
    output_profile = cog_profiles.get('deflate')
    output_profile["blockxsize"] = 256
    output_profile["blockysize"] = 256

    output_profile.update(dict(BIGTIFF="IF_SAFER"))

    with MemoryFile() as mem_dst:
        cog_translate(
            input,
            mem_dst.name,
            output_profile,
            in_memory=True,
            quiet=False
        )

        if upload is not None:
            return upload_file(mem_dst, upload)
        else:
            return None


def handler(event, context):
    temp_dir = tempfile.mkdtemp()

    try:
        inp = download_file(temp_dir, file_uri=event.get('s3_filename'))

        out_name = os.path.basename(event.get('s3_filename'));
        s3_path = to_cog(inp, upload=out_name)
    except:
        print(traceback.format_exc())

    try:
        shutil.rmtree(temp_dir)
    except:
        print(traceback.format_exc())

    res = {
        "s3_filename": s3_path,
        "collection": collection
    }

    if event.get('s3_datetime') is not None:
        res['s3_datetime'] = event.get('s3_datetime')
    if event.get('granule_id') is not None:
        res['granule_id'] = event.get('granule_id')
    if event.get('datetime_regex') is not None:
        res['datetime_regex'] = event.get('datetime_regex')

    print(res)

    return res


if __name__ == "__main__":
    sample_event = {
        "s3_filename": "s3://climatedashboard-data/delivery/GRDI/GRDI_cellsFilledMissingValues_Count.tif",
        "collection": "default"
    }

    handler(sample_event, {})
