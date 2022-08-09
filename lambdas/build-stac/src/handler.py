import json
import os
from sys import getsizeof
from typing import Any, Dict, TypedDict, Union
from uuid import uuid4

from pydantic.tools import parse_obj_as

import smart_open

from . import stac, events


class S3LinkOutput(TypedDict):
    stac_file_url: str


class StacItemOutput(TypedDict):
    stac_item: Dict[str, Any]


def handler(event: Dict[str, Any], context) -> Union[S3LinkOutput, StacItemOutput]:
    """
    Lambda handler for STAC Collection Item generation

    Arguments:
    event - object with event parameters to be provided in one of 2 formats.
        Format option 1 (with Granule ID defined to retrieve all metadata from CMR):
        {
            "collection": "OMDOAO3e",
            "s3_filename": "s3://climatedashboard-data/OMDOAO3e/OMI-Aura_L3-OMDOAO3e_2022m0120_v003-2022m0122t021759.he5.tif",
            "granule_id": "G2205784904-GES_DISC",
        }
        Format option 2 (with regex provided to parse datetime from the filename:
        {
            "collection": "OMDOAO3e",
            "s3_filename": "s3://climatedashboard-data/OMSO2PCA/OMSO2PCA_LUT_SCD_2005.tif",
            "filename_regex": "^(.*?)(_)([0-9][0-9][0-9][0-9])(.*?)(.tif)$",
        }

    """

    parsed_event = parse_obj_as(events.SupportedEvent, event)
    stac_item = stac.generate_stac(parsed_event).to_dict()

    # TODO: Remove this hack
    if s3_url := event.get("data_url"):
        stac_item["assets"]["cog_default"]["href"] = s3_url

    output: StacItemOutput = {"stac_item": stac_item}

    # Return STAC Item Directly
    if getsizeof(json.dumps(output)) < (256 * 1024):
        return output

    # Return link to STAC Item
    key = f"s3://{os.environ['BUCKET']}/{uuid4()}.json"
    with smart_open.open(key, "w") as file:
        file.write(json.dumps(stac_item))

    return {"stac_file_url": key}


if __name__ == "__main__":
    sample_event = {
        "collection": "nightlights-hd-monthly",
        "s3_filename": "s3://climatedashboard-data/delivery/BMHD_Maria_Stages/70001_BeforeMaria_Stage0_2017-07-21.tif",
        "filename_regex": "^.*.tif$",
        "granule_id": None,
        "datetime_range": None,
        "start_datetime": None,
        "end_datetime": None,
    }
    handler(sample_event, {})
