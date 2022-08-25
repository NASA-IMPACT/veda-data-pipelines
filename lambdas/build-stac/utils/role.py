import os

import boto3


def assume_role(session_name):
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=os.environ.get("EXTERNAL_ROLE_ARN"), RoleSessionName=session_name,
    )
    return creds["Credentials"]
