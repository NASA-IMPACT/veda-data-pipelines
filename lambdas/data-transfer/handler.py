import os

import boto3


TARGET_BUCKET = os.environ["BUCKET"]
MCP_ROLE_ARN = os.environ.get("MCP_ROLE_ARN")

def _parse_s3_object(s3_object):
    split = s3_object.strip("s3://").split("/")
    bucket, path, key = split[0], "/".join(split[1:-1]), split[-1]
    return bucket, path, key

def assume_role():
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=os.environ.get("MCP_ROLE_ARN"), RoleSessionName="delta-simple-ingest",
    )
    return creds["Credentials"]

def handler(event, context):
    creds = assume_role()
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
        source_s3.download_file(bucket, f"{path}/{name}", f"/tmp/{name}")
        target_s3.upload_file(f"/tmp/{name}", TARGET_BUCKET, f"{object.get('collection')}/{name}")
        object["data_url"] = f"s3://{TARGET_BUCKET}/{object.get('collection')}/{name}"

    return event
