import boto3
import json
import os

from typing import Dict

from pypgstac import pypgstac
from pypgstac.load import loadopt


s3_client = boto3.client('s3')

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

def handler(event, context):
    SECRET_NAME = os.environ["SECRET_NAME"]
    connection_params = get_secret(SECRET_NAME)
    connection_string = build_connection_string(connection_params)

    stac_temp_file_name = "/tmp/stac_item.json"
    
    if stac_item := event.get("stac_item"):
        with open(stac_temp_file_name, "w+") as f:
            json.dump(stac_item, f)
    elif file_url := event.get("stac_file_url"):
        bucket_and_path = file_url.replace("s3://", "").split("/")
        bucket, filepath = bucket_and_path[0], '/'.join(bucket_and_path[1:])
        s3_client.download_file(
            bucket, filepath, stac_temp_file_name
        )
    else:
        raise Exception("No stac_item or stac_file_url provided")

    if event.get("dry_run"):
        print("Dry run, not inserting, would have inserted:")
        print(open(stac_temp_file_name).read())
        return

    pypgstac.load(
        file=stac_temp_file_name,
        table=event.get("type", "items"),
        method=loadopt.upsert,
        dsn=connection_string,
    )

if __name__ == '__main__':
    filename = "example.ndjson"
    sample_event = {
        "stac_file_url": "example.ndjson",
        # or
        "stac_item": {
        },
        "type": "collections"
    }
    handler(sample_event, {})
