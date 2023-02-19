import json
import os
import re
import pprint
import boto3
from csv import DictReader
from urllib.parse import urlparse

def handler(event, context):
    inventory_url = event.get("inventory_url")
    parsed_url = urlparse(inventory_url, allow_fragments=False)
    bucket = parsed_url.netloc
    inventory_filename = parsed_url.path.strip("/")
    filename_regex = event.get("filename_regex", None)
    collection = event.get("collection")
    cogify = event.pop("cogify", False)

    # raise if no inventory url or collection are in the input

    # Read the file and queue each item
    s3client = boto3.client("s3")
    start_after = event.pop("start_after", 0)

    file_objs_size = 0
    payload = {**event, "cogify": cogify, "objects": []}

    local_filename = inventory_filename.split('/')[-1]
    print(bucket)
    print(inventory_filename)
    s3client.download_file(Bucket=bucket, Key=inventory_filename, Filename=local_filename)
    with open(local_filename, 'r') as f:
         dict_reader = DictReader(f)
         list_of_dict = list(dict_reader)
         for line_number, file_dict in enumerate(iterable=list_of_dict, start=start_after):
            # TODO make this configurable
            filename = file_dict['s3_path']
            if filename_regex and not re.match(filename_regex, filename):
                continue
            if file_objs_size > 230000:
                payload["start_after"] = start_after
                break
            file_obj = {
                "collection": collection,
                "remote_fileurl": f"{filename}",
                "upload": event.get("upload", False),
                "user_shared": event.get("user_shared", False),
                "properties": event.get('properties', None)
            }
            payload["objects"].append(file_obj)
            file_obj_size = len(json.dumps(file_obj, ensure_ascii=False).encode("utf8"))
            file_objs_size = file_objs_size + file_obj_size
            start_after = line_number
    print(json.dumps(payload, indent=2))
    #print(payload['objects'][0])
    return payload


if __name__ == "__main__":
    sample_event = {
        "collection": "icesat2-boreal",
        "inventory_url": "s3://maap-data-store-test/AGB_tindex_master.csv",
        "discovery": "inventory",
        "upload": True,
        "start_after": 794
    }

    handler(sample_event, {})
