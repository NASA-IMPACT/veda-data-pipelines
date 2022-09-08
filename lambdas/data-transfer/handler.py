import os
import traceback

import boto3
from botocore.errorfactory import ClientError


TARGET_BUCKET = os.environ["BUCKET"]


def _parse_s3_object(s3_object):
    split = s3_object.strip("s3://").split("/")
    bucket, path, key = split[0], "/".join(split[1:-1]), split[-1]
    return bucket, path, key


def assume_role(role_arn, session_name):
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=role_arn, RoleSessionName=session_name,
    )
    return creds["Credentials"]


def handler(event, context):
    kwargs = {}
    if role_arn := os.environ.get("EXTERNAL_ROLE_ARN"):
        creds = assume_role(role_arn, "veda-data-pipelines_data-transfer")
        kwargs = {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds["SecretAccessKey"],
            "aws_session_token": creds["SessionToken"],
        }
    source_s3 = boto3.client("s3")
    target_s3 = boto3.client(
        "s3",
        **kwargs
    )
    for object in event:
        if not object.get("upload"):
            continue
        bucket, path, name = _parse_s3_object(object["s3_filename"])
        tmp_filename = f"/tmp/{name}"

        target_key = f"{object.get('collection')}/{name}"
        target_url = f"s3://{TARGET_BUCKET}/{target_key}"

        # Check if the corresponding object exists in the target bucket
        try:
            target_s3.head_object(Bucket=TARGET_BUCKET, Key=target_key)
        except ClientError as ce:
            try:
                # Not found
                source_s3.download_file(bucket, f"{path}/{name}", tmp_filename)
                target_s3.upload_file(tmp_filename, TARGET_BUCKET, target_key)
                # Clean up the data
                if os.path.exists(tmp_filename):
                    os.remove(tmp_filename)
            except Exception as internal_exception:
                print(f"Failed while trying to upload missing file at s3://{bucket}/{target_key}.")
                traceback.print_exception(type(ce), ce, ce.__traceback__)
                raise Exception(ce, internal_exception)

        object["s3_filename"] = target_url

    return event
