import asyncio
import json
import os
from typing import Dict

import boto3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from pypgstac.load import load_ndjson, loadopt


def get_secret(secret_name: str):
    """Get Secrets from secret manager."""
    client = boto3.client(service_name="secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


def build_connection_string(connection_params: Dict):
    connection_string = (
        f"postgresql://{connection_params['username']}:"
        f"{connection_params['password']}@"
        f"{connection_params['host']}:"
        f"{connection_params['port']}/"
        f"{connection_params.get('dbname', 'postgres')}"
    )
    return connection_string


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context):
    SECRET_NAME = os.environ["SECRET_NAME"]
    connection_params = get_secret(SECRET_NAME)
    connection_string = build_connection_string(connection_params)
    for record in event.records:
        print(record.body)
        asyncio.run(
            load_ndjson(
                file=record.body,
                table="items",
                method=loadopt.upsert,
                dsn=connection_string,
            )
        )

filename = "example.ndjson"
sample_event = SQSEvent({
    "Records": [{
        "Body": filename
    }]
})
handler(sample_event, {})