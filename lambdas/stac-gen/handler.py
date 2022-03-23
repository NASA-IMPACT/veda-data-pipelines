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
    )
    return stac_item

def get_maria_dt(url):
    if 'Stage0' in url:
        start = str_to_datetime('2017-07-21')
        end = str_to_datetime('2017-09-19')
    elif 'Stage1' in url:
        start = str_to_datetime('2017-09-20')
        end = str_to_datetime('2017-11-20')
    elif 'Stage2' in url:
        start = str_to_datetime('2017-11-21')
        end = str_to_datetime('2018-01-20')
    elif 'Stage3' in url:
        start = str_to_datetime('2018-01-21')
        end = str_to_datetime('2018-03-20')
    else:
        raise Exception('Invalid')

    return {
        "start_datetime": start.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "end_datetime": end.strftime('%Y-%m-%dT%H:%M:%SZ')
    }

def create_stac_item_with_regex(event):
    """
    Function to create a STAC item using a user provided regex to parse datetime from a filename
    """

    cog_url = event["s3_filename"]
    collection = event["collection"]
    assets = {}

    # For maria
    """
    properties = get_maria_dt(cog_url)
    dt = None
    """

    # For non maria
    properties = {}
    datetime_regex = re.compile(event["datetime_regex"]["regex"])
    try:
        match = datetime_regex.match(cog_url)
        print(match)
        elements = [match.group(g) for g in event["datetime_regex"]["target_group"]]
        print(elements)
        datestring = "-".join(elements)
        print(datestring)
        dt = str_to_datetime(datestring)
    except Exception as e:
        print(f"Could not parse date string from filename: {cog_url}")
        return e

    stac_item = create_item(
        properties=properties,
        assets=assets,
        datetime=dt,
        cog_url=cog_url,
        collection=collection,
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
            "datetime_regex": {
                "regex": "^(.*?)(_)([0-9][0-9][0-9][0-9])(.*?)(.tif)$",
                # target_group is the group that contains the datetime string when the original filename is matched on the user provided regex
                "target_group": 3
            }
        }

    """
    try:
        if "granule_id" in event:
            if "datetime_regex" in event:
                raise Exception(
                    "Either granule_id or datetime_regex must be provided, not both."
                )
                # Only granule_id provided, look up in CMR
                stac_item = create_stac_item_with_cmr(event)
        elif "datetime_regex" in event:
            if "granule_id" in event:
                raise Exception(
                    "Either granule_id or datetime_regex must be provided, not both."
                )
            else:
                if not isinstance(event["datetime_regex"]["target_group"], list):
                    raise Exception(
                        "Target group should be specified as a a list. Ex. [3]"
                    )

                stac_item = create_stac_item_with_regex(event)
        else:
            raise Exception("Either granule_id or datetime_regex must be provided")
    except Exception as e:
        print(e)
        return

    try:
        stac_dict = stac_item.to_dict()
        print(stac_dict)
        upload_stac_to_s3(stac_dict)
    except Exception as e:
        print(e)
        return e

    return {"stac_item": stac_dict}


if __name__ == "__main__":
    sample_event = {
        "collection": "BMHD_Maria",
        # "s3_filename": "s3://climatedashboard-data/OMDOAO3e/OMI-Aura_L3-OMDOAO3e_2022m0120_v003-2022m0122t021759.he5.tif",
        # "granule_id": "G2205784904-GES_DISC",
        "s3_filename": "s3://climatedashboard-data/BMHD_Maria_Stages/Maria_Stage3.tif",
        "datetime_regex": {
            "regex": "^(.*?BMHD_Ida)([0-9][0-9][0-9][0-9])(.*?)(_)([A-Za-z]+[0-9])(.tif)$",
            "target_group": [3],
        },
    }

    handler(sample_event, {})
