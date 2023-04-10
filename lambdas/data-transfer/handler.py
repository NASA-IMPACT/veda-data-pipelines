import json
import os
import urllib.parse
import tempfile

import boto3
from botocore.errorfactory import ClientError


def assume_role(role_arn, session_name):
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
    )
    return creds["Credentials"]


def handler(event, context):
    TARGET_BUCKET = os.environ["BUCKET"]

    kwargs = {}
    if role_arn := os.environ.get("DATA_MANAGEMENT_ROLE_ARN"):
        creds = assume_role(role_arn, "veda-data-pipelines_data-transfer")
        kwargs = {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds["SecretAccessKey"],
            "aws_session_token": creds["SessionToken"],
        }
    source_s3 = boto3.client("s3", **kwargs)
    target_s3 = boto3.client("s3", **kwargs)

    for object in event:
        if not object.get("upload"):
            continue

        if object.get("user_shared"):
            TARGET_BUCKET = os.environ.get("USER_SHARED_BUCKET")

        url = urllib.parse.urlparse(object["remote_fileurl"])
        src_bucket = url.hostname
        src_key = url.path.strip("/")
        filename = src_key.split("/")[-1]

        target_key = f"{object.get('collection')}/{filename}"
        # The file-staging directory is the default for MAAP's bucket
        directory = object.get("directory", "file-staging")
        if directory:
            target_key = f"{directory}/{target_key}"
        target_url = f"s3://{TARGET_BUCKET}/{target_key}"

        # Check if the corresponding object exists in the target bucket
        try:
            target_s3.head_object(Bucket=TARGET_BUCKET, Key=target_key)
        except ClientError:
            try:
                # Not found
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_filename = f"{tmp_dir}/{filename}"
                    source_s3.download_file(src_bucket, src_key, tmp_filename)
                    target_s3.upload_file(tmp_filename, TARGET_BUCKET, target_key)
            except:
                print(
                    "Failed while trying to upload file from "
                    f"s3://{src_bucket}/{src_key} to s3://{TARGET_BUCKET}/{target_key}."
                )
                raise

        object["remote_fileurl"] = target_url

    return event


if __name__ == "__main__":
    sample_event = [
        {
            "collection": "icesat2-boreal",
            "remote_fileurl": "s3://maap-ops-workspace/lduncanson/dps_output/run_boreal_biomass_quick_v2_ubuntu/map_boreal_2022_rh_noground_v4/2023/02/07/17/26/40/509524/boreal_agb_202302071675790681_27635.tif",
            "upload": True,
            "user_shared": False,
            "properties": None,
        }
    ]

    print(json.dumps(handler(sample_event, {}), indent=2))
