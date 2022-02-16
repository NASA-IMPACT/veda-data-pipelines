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

    return stac_json

if __name__ == "__main__":
    sample_event = (
        {
            "stac_item": {
                "assets": {
                    "cog": {
                        "href": "s3://climatedashboard-data/BMHD_Ida/BMHD_Ida2021_NO_LA_August9.tif",
                        "roles": ["data"],
                        "title": "COG",
                        "type": "image/tiff; application=geotiff",
                    }
                },
                "bbox": [
                    -90.3037818244749,
                    29.804659612978707,
                    -89.87578181971654,
                    30.07177072705947,
                ],
                "collection": "BMHD_Ida",
                "geometry": {
                    "coordinates": [
                        [
                            [-90.3037818244749, 30.07177072705947],
                            [-90.3037818244749, 29.804659612978707],
                            [-89.87578181971654, 29.804659612978707],
                            [-89.87578181971654, 30.07177072705947],
                            [-90.3037818244749, 30.07177072705947],
                        ]
                    ],
                    "type": "Polygon",
                },
                "id": "BMHD_Ida2021_NO_LA_August9.tif",
                "links": [
                    {
                        "href": "BMHD_Ida",
                        "rel": "collection",
                        "type": "application/json",
                    }
                ],
                "properties": {
                    "datetime": "2021-08-09T00:00:00Z",
                    "proj:bbox": [
                        -90.3037818244749,
                        29.804659612978707,
                        -89.87578181971654,
                        30.07177072705947,
                    ],
                    "proj:epsg": 4326,
                    "proj:geometry": {
                        "coordinates": [
                            [
                                [-90.3037818244749, 30.07177072705947],
                                [-90.3037818244749, 29.804659612978707],
                                [-89.87578181971654, 29.804659612978707],
                                [-89.87578181971654, 30.07177072705947],
                                [-90.3037818244749, 30.07177072705947],
                            ]
                        ],
                        "type": "Polygon",
                    },
                    "proj:shape": [2404, 3852],
                    "proj:transform": [
                        0.00011111111234640703,
                        0.0,
                        -90.3037818244749,
                        0.0,
                        -0.00011111111234640703,
                        30.07177072705947,
                        0.0,
                        0.0,
                        1.0,
                    ],
                },
                "stac_extensions": [
                    "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
                    "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
                ],
                "stac_version": "1.0.0",
                "type": "Feature",
            }
        },
    )

    handler(sample_event, {})
