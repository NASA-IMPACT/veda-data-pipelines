import json
import os
import re
import pprint
import boto3
from csv import DictReader
from urllib.parse import urlparse


def assume_role(role_arn, session_name):
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
    )
    return creds["Credentials"]


def handler(event, context):
    inventory_url = event.get("inventory_url")
    file_url_key = event.get("file_url_key", "s3_path")
    parsed_url = urlparse(inventory_url, allow_fragments=False)
    bucket = parsed_url.netloc
    inventory_filename = parsed_url.path.strip("/")
    filename_regex = event.get("filename_regex", None)
    collection = event.get("collection")
    cogify = event.pop("cogify", False)

    # raise if no inventory url or collection are in the input

    # Read the file and queue each item
    kwargs = {}
    if role_arn := os.environ.get("DATA_MANAGEMENT_ROLE_ARN"):
        creds = assume_role(role_arn, "veda-data-pipelines_s3-discovery")
        kwargs = {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds["SecretAccessKey"],
            "aws_session_token": creds["SessionToken"],
        }
    s3client = boto3.client("s3", **kwargs)
    start_after = event.pop("start_after", 0)

    file_objs_size = 0
    payload = {**event, "cogify": cogify, "objects": []}

    local_filename = f"/tmp/{inventory_filename.split('/')[-1]}"
    s3client.download_file(
        Bucket=bucket, Key=inventory_filename, Filename=local_filename
    )
    with open(local_filename, "r") as f:
        dict_reader = DictReader(f)
        list_of_dict = list(dict_reader)
        for file_dict in list_of_dict[start_after:]:
            filename = file_dict[file_url_key]
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
                "properties": event.get("properties", None),
            }
            payload["objects"].append(file_obj)
            file_obj_size = len(json.dumps(file_obj, ensure_ascii=False).encode("utf8"))
            file_objs_size = file_objs_size + file_obj_size
            start_after += 1
    # For testing purposes:
    # print(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    sample_event = {
        "collection": "icesat2-boreal",
        "inventory_url": "s3://maap-data-store-test/AGB_tindex_master.csv",
        "discovery": "inventory",
        "file_url_key": "s3_path",
        "upload": True,
    }

    handler(sample_event, {})
