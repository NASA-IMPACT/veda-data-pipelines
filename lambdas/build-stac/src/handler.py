import json
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from uuid import uuid4

from cmr import GranuleQuery
from pydantic import BaseModel
import pystac
from pystac.utils import str_to_datetime
from pydantic.tools import parse_obj_as

from rio_stac import stac
from smart_open import open

from . import utils


def create_item(
    properties,
    datetime,
    cog_url,
    collection,
    assets=None,
    asset_name=None,
    asset_roles=None,
    asset_media_type=None,
) -> pystac.Item:
    """
    Function to create a stac item from a COG using rio_stac
    """
    return stac.create_stac_item(
        id=Path(cog_url).stem,
        source=cog_url,
        collection=collection,
        input_datetime=datetime,
        properties=properties,
        with_proj=True,
        with_raster=True,
        assets=assets,
        # TODO (aimee):
        # If we want to have multiple assets _and_ the raster stats from get_raster_info we need to make this conditional more flexible:
        # https://github.com/developmentseed/rio-stac/blob/0.3.2/rio_stac/stac.py#L315-L330
        asset_name=asset_name or "cog_default",
        asset_roles=asset_roles or ["data", "layer"],
        asset_media_type=(
            asset_media_type
            or "image/tiff; application=geotiff; profile=cloud-optimized"
        ),
    )


class BaseEvent(BaseModel, frozen=True):
    collection: str
    s3_filename: str

    asset_name: Optional[str] = None
    asset_roles: Optional[List[str]] = None
    asset_media_type: Optional[Union[str, pystac.MediaType]] = None


class CmrEvent(BaseEvent):
    granule_id: str

    def as_stac(self) -> pystac.Item:
        """
        Generate STAC Item from CMR granule
        """
        cmr_json = GranuleQuery().concept_id(self.granule_id).get(1)[0]
        return create_item(
            properties=cmr_json,
            datetime=str_to_datetime(cmr_json["time_start"]),
            cog_url=self.s3_filename,
            collection=self.collection,
            asset_name=self.asset_name,
            asset_roles=self.asset_roles,
            asset_media_type=self.asset_media_type,
        )


class RegexEvent(BaseEvent):
    filename_regex: str

    properties: Optional[Dict] = {}
    datetime_range: Optional[utils.INTERVAL] = None

    def as_stac(self) -> pystac.Item:
        """
        Generate STAC item from user provided regex & filename
        """

        start_datetime, end_datetime, single_datetime = utils.extract_dates(
            self.s3_filename, self.datetime_range
        )

        if start_datetime and end_datetime:
            self.properties["start_datetime"] = f"{start_datetime.isoformat()}Z"
            self.properties["end_datetime"] = f"{end_datetime.isoformat()}Z"
            single_datetime = None

        return create_item(
            properties=self.properties,
            datetime=single_datetime,
            cog_url=self.s3_filename,
            collection=self.collection,
            asset_name=self.asset_name,
            asset_roles=self.asset_roles,
            asset_media_type=self.asset_media_type,
        )


Event = Union[RegexEvent, CmrEvent]


def handler(event: Dict[str, Any], context):
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
            "filename_regex": "^(.*?)(_)([0-9][0-9][0-9][0-9])(.*?)(.tif)$",
        }

    """

    stac_item = parse_obj_as(Event, event).as_stac()
    stac_dict = stac_item.to_dict()

    # TODO: Remove this hack
    if s3_url := event.get("data_url"):
        stac_dict["assets"]["cog_default"]["href"] = s3_url

    key = f"s3://{os.environ['BUCKET']}/{uuid4()}.json"
    with open(key, "w") as file:
        file.write(json.dumps(stac_dict))

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
