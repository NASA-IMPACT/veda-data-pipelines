import os

import boto3
from botocore.errorfactory import ClientError


TARGET_BUCKET = os.environ["BUCKET"]
EXTERNAL_ROLE_ARN = os.environ.get("EXTERNAL_ROLE_ARN")


def _parse_s3_object(s3_object):
    split = s3_object.strip("s3://").split("/")
    bucket, path, key = split[0], "/".join(split[1:-1]), split[-1]
    return bucket, path, key


def assume_role(session_name):
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=os.environ.get("EXTERNAL_ROLE_ARN"), RoleSessionName=session_name,
    )
    return creds["Credentials"]


def handler(event, context):
    creds = assume_role("delta-simple-ingest")
    source_s3 = boto3.client("s3")
    target_s3 = boto3.client(
        "s3",
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
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
        except ClientError:
            # Not found
            source_s3.download_file(bucket, f"{path}/{name}", tmp_filename)
            target_s3.upload_file(tmp_filename, TARGET_BUCKET, target_key)
            # Clean up the data
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

        object["data_url"] = target_url

    return event
