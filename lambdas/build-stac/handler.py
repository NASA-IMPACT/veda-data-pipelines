import json
import os
from sys import getsizeof
from typing import Any, Dict, TypedDict, Union
from uuid import uuid4

import smart_open

from utils import stac, events


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
        }

    """

    EventType = events.CmrEvent if event.get("granule_id") else events.RegexEvent
    parsed_event = EventType.parse_obj(event)
    stac_item = stac.generate_stac(parsed_event).to_dict()
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
        "collection": "ABLVIS1B",
        "s3_filename": "s3://nasa-maap-data-store/file-staging/nasa-map/ABLVIS1B___001/LVIS1B_ABoVE2017_0629_R1803_056233.h5",
        "granule_id": "G1200116875-NASA_MAAP",
        "id": "G1200116875-NASA_MAAP",
        "mode": "cmr"
    }  
    print(json.dumps(handler(sample_event, {}), indent=2))
