from cmr import GranuleQuery
import os
import json
import pystac
from pystac.utils import str_to_datetime
from shapely.geometry import shape
from pypgstac import pypgstac
from rio_stac.stac import bbox_to_geom, create_stac_item
import re
import sys

STAC_DB_HOST = os.environ.get("STAC_DB_HOST")
STAC_DB_USER = os.environ.get("STAC_DB_USER")
STAC_DB_PASSWORD = os.environ.get("STAC_DB_PASSWORD")

def handler(event, context):
    """
    Simple Lambda that should belong to the VPC of the STAC_DB_HOST
    Receive a STAC item in JSON format, connect to database and insert it
    """
    stac_json = event["stac_item"]
    # pypgstac requires inserting from a file
    with open("/tmp/temp.json", "w+") as f:
        f.write(json.dumps(stac_json))

    try:
        pypgstac.load(
            table="items",
            file="/tmp/temp.json",
            dsn=f"postgres://{STAC_DB_USER}:{STAC_DB_PASSWORD}@{STAC_DB_HOST}/postgis",
            method="insert_ignore",  # use insert_ignore to avoid overwritting existing items
        )
        print("Inserted to database")
    except Exception as e:
        print(e)
        return e
    os.remove("/tmp/temp.json")

    return stac_dict


if __name__ == "__main__":
    sample_event = {
        "stac_item": {
            "id": 1
        }
    },

    handler(sample_event, {})
