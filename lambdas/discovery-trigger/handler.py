import os
import json

import boto3


def handler(event, context):
    STEP_FUNCTION_ARN = os.environ["STEP_FUNCTION_ARN"]

    event.pop("objects", None)

    client = boto3.client("stepfunctions")
    client.start_execution(
        stateMachineArn=STEP_FUNCTION_ARN,
        input=json.dumps(event),
    )
    return
