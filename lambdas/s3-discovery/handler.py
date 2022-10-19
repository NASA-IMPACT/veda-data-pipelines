import json
import os
import re

import boto3


def assume_role(role_arn, session_name):
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
    )
    return creds["Credentials"]


def handler(event, context):
    bucket = event.get("bucket")
    prefix = event.get("prefix", "")
    filename_regex = event.get("filename_regex", None)
    collection = event.get("collection", prefix.rstrip("/"))
    properties = event.get("properties", {})
    cogify = event.pop("cogify", False)

    if role_arn := os.environ.get("EXTERNAL_ROLE_ARN"):
        creds = assume_role(role_arn, "veda-data-pipelines_s3-discovery")
        kwargs = {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds["SecretAccessKey"],
            "aws_session_token": creds["SessionToken"],
        }
    s3client = boto3.client("s3", **kwargs)
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
    for page in pages:
        for obj in page["Contents"]:
            # The limit is advertised at 256000, but we'll preserve some breathing room
            if file_objs_size > 230000:
                payload["start_after"] = start_after
                break
            filename = obj["Key"]
            if filename_regex and not re.match(filename_regex, filename):
                continue
            file_obj = {
                "collection": collection,
                "s3_filename": f"s3://{bucket}/{filename}",
                "upload": event.get("upload", False),
                "properties": properties,
            }
            payload["objects"].append(file_obj)
            file_obj_size = len(json.dumps(file_obj, ensure_ascii=False).encode("utf8"))
            file_objs_size = file_objs_size + file_obj_size
            start_after = filename
    return payload


if __name__ == "__main__":
    sample_event = {
        "bucket": "climatedashboard-data",
        "prefix": "social_vulnerability_index/",
        "filename_regex": "^(.*)_housing_(.*)$",
        "collection": "social-vulnerability-index-housing",
        "upload": True,
        "cogify": False,
    }

    handler(sample_event, {})
