import os
import json
from pypgstac import pypgstac
import boto3

STAC_DB_HOST = os.environ.get("STAC_DB_HOST")
STAC_DB_USER = os.environ.get("STAC_DB_USER")
PGPASSWORD = os.environ.get("PGPASSWORD")

s3_client = boto3.client('s3')

def handler(event, context):
    """
    Simple Lambda that should belong to the VPC of the STAC_DB_HOST
    Receive a STAC item in JSON format, connect to database and insert it
    """
    stac_temp_file_name = "/tmp/stac_item.json"

    if "stac_item" in event:
        stac_json = event["stac_item"]
        print(stac_json)
        with open(stac_temp_file_name, "w+") as f:
            json.dump(stac_json, f)
    elif "stac_file_url" in event:
        s3_client.download_file(
            "climatedashboard-data", event["stac_file_url"], stac_temp_file_name
        )
        print(open(stac_temp_file_name).read())
    # pypgstac requires inserting from a file

    try:
        pypgstac.load(
            table=event.get("type", "items"),
            file=stac_temp_file_name,
            dsn=f"postgres://{STAC_DB_USER}:{PGPASSWORD}@{STAC_DB_HOST}/postgis",
            # use upsert
            method="upsert",  # use insert_ignore to avoid overwritting existing items
        )
        print("Inserted to database")
    except Exception as e:
        print(e)
        return e
    os.remove(stac_temp_file_name)


if __name__ == "__main__":
    sample_item = json.load(open("sample-stac-item.json", "r"))

    sample_download = {
        "stac_file_url": "stac_item_queue/Maria_Stage3.json",
        "type": "items"
    }

    sample_item_event = {
        "stac_item": sample_item,
        "type": "collections"
    }

    handler(sample_item_event, {})
