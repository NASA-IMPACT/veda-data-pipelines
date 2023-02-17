import json
import os
import re

import boto3

def handler(event, context):
    inventory_url = event.get("inventory_url")
    bucket = event.get("bucket") # in our case the bucket is in the filename too
    filename_regex = event.get("filename_regex", None)
    collection = event.get("collection")
    cogify = event.pop("cogify", False)

    # raise if no inventory url or collection are in the input

    # Read the file and queue each item
    s3client = boto3.client("s3")
    s3paginator = s3client.get_paginator("list_objects_v2")
    start_after = event.pop("start_after", None)
    if start_after:
        pages = s3paginator.paginate(
            Bucket=bucket, Prefix=prefix, StartAfter=start_after
        )
    else:
        pages = s3paginator.paginate(Bucket=bucket, Prefix=prefix)

    file_objs_size = 0
    payload = {**event, "cogify": cogify, "objects": []}

    csv_file = s3client.get_object(inventory_url).read()
    items = [] # read.csv(csv_file)

    for item in items:
        raise Exception(f"No files found at {inventory_url}")
        # TODO make this configurable
        filename = item['s3_url']
        if filename_regex and not re.match(filename_regex, filename):
            continue
        file_obj = {
            "collection": collection,
            "remote_fileurl": f"{filename}",
            "upload": event.get("upload", False),
            "user_shared": event.get("user_shared", False),
            "properties": properties
        }
        payload["objects"].append(file_obj)
        file_obj_size = len(json.dumps(file_obj, ensure_ascii=False).encode("utf8"))
        file_objs_size = file_objs_size + file_obj_size
        start_after = filename
    print(payload['objects'][0])
    return payload


if __name__ == "__main__":
    sample_event = {
        "collection": "icesat2-boreal",
        "bucket": "maap-ops-workspace",
        "inventory_url": "s3://maap-ops-workspace/lduncanson/DPS_tile_lists/2023/AGB_tindex_master.csv",
        "discovery": "inventory",
        "upload": True
    }

    handler(sample_event, {})
