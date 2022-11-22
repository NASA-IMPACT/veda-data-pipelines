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


def list_bucket(bucket, prefix, filename_regex):
    kwargs = {}
    if role_arn := os.environ.get("DATA_MANAGEMENT_ROLE_ARN"):
        creds = assume_role(role_arn, "veda-data-pipelines_s3-discovery")
        kwargs = {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds["SecretAccessKey"],
            "aws_session_token": creds["SessionToken"],
        }
    s3 = boto3.resource("s3", **kwargs)
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

    except:
        print("Failed during s3 item/asset discovery")
        raise


def handler(event, context):
    bucket = event.pop("bucket")
    prefix = event.pop("prefix", "")

    filenames = list_bucket(
        bucket=bucket, prefix=prefix, filename_regex=event.pop("filename_regex", None)
    )

    files_objs = []
    cogify = event.pop("cogify", False)
    collection = event.get("collection", prefix.rstrip("/"))
    for filename in filenames:
        files_objs.append(
            {
                **event,
                "collection": collection,
                "s3_filename": f"s3://{bucket}/{filename}",
                "upload": event.get("upload", False),
            }
        )
    return {
        "cogify": cogify,
        "objects": files_objs,
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
