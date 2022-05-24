import json
import os

import boto3


COGIFY_QUEUE_URL = os.environ.get("COGIFY_QUEUE_URL")
STAC_READY_URL = os.environ.get("STAC_READY_URL")

QUEUE = {
    True: COGIFY_QUEUE_URL,
    False: STAC_READY_URL
}

def handler(event, context):
    client = boto3.client("sqs")
    for item_url in event.get("objects"):
        client.send_message(
            QueueUrl=QUEUE[bool(event.get("cogify", False))],
            MessageBody=json.dumps(item_url)
        )


if __name__ == "__main__":
    sample_event = {
        "cogify": True,
        "objects": []
    }

    handler(sample_event, {})
