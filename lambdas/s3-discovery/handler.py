import os
import re

import boto3


def assume_role(session_name):
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=os.environ.get("EXTERNAL_ROLE_ARN"),
        RoleSessionName=session_name,
    )
    return creds["Credentials"]


def list_bucket(bucket, prefix, filename_regex):
    creds = assume_role("delta-s3-discovery")
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
    try:
        files = []
        bucket = s3.Bucket(bucket)
        for obj in bucket.objects.filter(Prefix=prefix):
            if filename_regex:
                if re.match(filename_regex, obj.key):
                    files.append(obj.key)
            else:
                files.append(obj.key)
        return files

    except Exception as e:
        print(e)
        return e


def handler(event, context):
    filenames = list_bucket(
        bucket=event["bucket"], prefix=event.get("prefix"), filename_regex=event.get("filename_regex")
    )

    files_objs = []
    cogify = event.pop("cogify", False)
    bucket = event.get("bucket")
    collection = event.get("collection", event["prefix"][:-1])
    for filename in filenames:
        files_objs.append(
            {
                "filename_regex": event.get("filename_regex"),
                "datetime_range": event.get("datetime_range"),

                "single_datetime": event.get("single_datetime"),
                "start_datetime": event.get("start_datetime"),
                "end_datetime": event.get("end_datetime"),

                "properties": event.get("properties"),

                "collection": collection,
                "s3_filename": f's3://{bucket}/{filename}',
                "href": f's3://{bucket}/{filename}',
                "id": filename,
                "upload": event.get("upload", False),
            }
        )
    return {
        "cogify": cogify,
        "objects": files_objs
    }


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
