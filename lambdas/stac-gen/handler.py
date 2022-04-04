import boto3
import json
import os
import pystac
import re
import sys

from cmr import GranuleQuery
from pathlib import Path
from pypgstac import pypgstac
from pystac.utils import str_to_datetime
from rio_stac.stac import bbox_to_geom, create_stac_item
from shapely.geometry import shape


s3 = boto3.client(
    "s3",
)

ASSET_NAME = "cog_default"
ASSET_ROLE = ["data", "layer"]
ASSET_MEDIA_TYPE = "image/tiff; application=geotiff; profile=cloud-optimized"
DATE_REGEX = re.compile("\d{4}-\d{2}-\d{2}")

STAC_DB_HOST = os.environ.get("STAC_DB_HOST")
STAC_DB_USER = os.environ.get("STAC_DB_USER")
PGPASSWORD = os.environ.get("PGPASSWORD")


def upload_stac_to_s3(stac_dict):
    fname = stac_dict["id"].split(".tif")[0]
    with open(f"/tmp/{fname}.json", "w+") as f:
        f.write(json.dumps(stac_dict))
    try:
        s3.upload_file(
            f"/tmp/{fname}.json",
            "climatedashboard-data",
            f"stac_item_queue/{fname}.json",
        )
        print("File uploaded to s3")
        return f"s3://climatedashboard-data/stac_item_queue/{fname}.json"
    except Exception as e:
        print("Failed to copy to S3 bucket")
        print(e)
        return None


def create_item(
    properties,
    assets,
    datetime,
    cog_url,
    collection,
    asset_name=None,
    asset_roles=None,
    asset_media_type=None
):
    """
    Function to create a stac item from a COG using rio_stac
    """
    asset_name = asset_name or ASSET_NAME
    asset_roles = asset_roles or ASSET_ROLE
    asset_media_type = asset_media_type or ASSET_MEDIA_TYPE
    try:
        item_id = Path(cog_url).stem
        rstac = create_stac_item(
            id=item_id,
            source=cog_url,
            collection=collection,
            input_datetime=datetime,
            properties=properties,
            with_proj=True,
            with_raster=True,
            # TODO (aimee):
            # If we want to have multiple assets _and_ the raster stats from get_raster_info we need to make this conditional more flexible:
            # https://github.com/developmentseed/rio-stac/blob/0.3.2/rio_stac/stac.py#L315-L330
            asset_name=asset_name,
            asset_roles=asset_roles,
            asset_media_type=asset_media_type,
        )
        print("Created item...")
    except Exception as e:
        print(e)
        return f"failed to produce stac item for {cog_url}"

    return rstac


def extract_dates(filename):
    """
    Extracts start, end, or single date string from filename
    and convert it to iso format datetime.
    """
    dates = DATE_REGEX.findall(filename)
    start_datetime = None
    end_datetime = None
    single_datetime = None
    total_dates = len(dates)
    if total_dates > 1:
        start_datetime = str_to_datetime(dates[0])
        end_datetime = str_to_datetime(dates[-1])
    elif total_dates == 1:
        single_datetime = str_to_datetime(dates[0])
    elif total_dates == 0:
        raise Exception("No dates provided in filename. Atleast one date in format yyyy-mm-dd is required.")
    return start_datetime, end_datetime, single_datetime


def create_stac_item_with_cmr(event):
    """
    Function to query CMR for metadata and create a stac item
    """
    api = GranuleQuery()

    concept_id = event["granule_id"]
    cmr_json = api.concept_id(concept_id).get(1)[0]

    cog_url = event["s3_filename"]
    collection = event["collection"]

    assets = {}

    for link in cmr_json["links"]:
        if ".he5" in link["href"]:
            name = link["title"] if "title" in link else link["href"]
            assets[name] = pystac.Asset(
                href=link["href"],
                media_type="application/x-hdf5",
                roles=["data"],
                title="hdf image",
            )

    dt = str_to_datetime(cmr_json["time_start"])

    stac_item = create_item(
        properties=cmr_json,
        assets=assets,
        datetime=dt,
        cog_url=cog_url,
        collection=collection,
        asset_name=event.get("asset_name"),
        asset_roles=event.get("asset_roles"),
        asset_media_type=event.get("asset_media_type")
    )
    return stac_item

def create_stac_item_with_regex(event):
    """
    Function to create a STAC item using a user provided regex to parse datetime from a filename
    """

    cog_url = event["s3_filename"]
    collection = event["collection"]
    assets = {}

    properties = event.get("properties", {})
    try:
        start_datetime, end_datetime, single_datetime = extract_dates(cog_url)
        if start_datetime and end_datetime:
            properties['start_datetime'] = start_datetime
            properties['end_datetime'] = end_datetime

    except Exception as e:
        print(f"Could not parse date string from filename: {cog_url}")
        return e

    stac_item = create_item(
        properties=event.get("properties", {}),
        assets=assets,
        datetime=dt,
        cog_url=cog_url,
        collection=collection,
        asset_name=event.get("asset_name"),
        asset_roles=event.get("asset_roles"),
        asset_media_type=event.get("asset_media_type")
    )

    return stac_item


def handler(event, context):
    """
    Lambda handler for STAC Collection Item generation

    Arguments:
    event - object with event parameters to be provided in one of 2 formats.
         Format option 1 (with Granule ID defined to retrieve all  metadata from CMR):
        {
           "collection": "OMDOAO3e",
            "s3_filename": "s3://climatedashboard-data/OMDOAO3e/OMI-Aura_L3-OMDOAO3e_2022m0120_v003-2022m0122t021759.he5.tif",
            "granule_id": "G2205784904-GES_DISC",
        }
        Format option 2 (with regex provided to parse datetime from the filename:
        {
           "collection": "OMDOAO3e",
            "s3_filename": "s3://climatedashboard-data/OMSO2PCA/OMSO2PCA_LUT_SCD_2005.tif",
            "filename_regex": {
                "regex": "^(.*?)(_)([0-9][0-9][0-9][0-9])(.*?)(.tif)$",
            }
        }

    """
    try:
        granule_id = event.get("granule_id")
        datetime_holder = event.get("filename_regex")

        if granule_id and datetime_holder:
            raise Exception(
                "Either granule_id or filename_regex must be provided, not both."
            )

        if granule_id:
            # Only granule_id provided, look up in CMR
            stac_item = create_stac_item_with_cmr(event)
        elif datetime_holder:
            stac_item = create_stac_item_with_regex(event)
        else:
            raise Exception("Either granule_id or filename_regex must be provided")
    except Exception as e:
        print(e)
        return
    try:
        stac_dict = stac_item.to_dict()
        upload_stac_to_s3(stac_dict)
    except Exception as e:
        return e

    return {"stac_item": stac_dict}


if __name__ == "__main__":
    sample_event = {
        "collection": "social-vulnerability-index-housing",
        "s3_filename": "s3://climatedashboard-data/social_vulnerability_index/svi_2000-01-01-2000-02-02_tract_housing_wgs84_cog.tif",
        "filename_regex": {
            "regex": "^(.*?)_(\\d{4})_(.*?).tif$",
        },
        "properties": {}
    }

    handler(sample_event, {})
