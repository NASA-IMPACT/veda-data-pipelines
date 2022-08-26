from pathlib import Path
from functools import singledispatch

from cmr import GranuleQuery
import pystac
from pystac.utils import str_to_datetime

from rio_stac import stac

from . import regex, events


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


@singledispatch
def generate_stac(item) -> pystac.Item:
    raise Exception(f"Unsupport event type: {type(item)=}, {item=}")


@generate_stac.register
def generate_stac_regexevent(item: events.RegexEvent) -> pystac.Item:
    """
    Generate STAC item from user provided regex & filename
    """
    start_datetime, end_datetime, single_datetime = regex.extract_dates(
        item.s3_filename, item.datetime_range
    )

    if start_datetime and end_datetime:
        item.properties["start_datetime"] = start_datetime.isoformat()
        item.properties["end_datetime"] = end_datetime.isoformat()
        single_datetime = None

    return create_item(
        properties=item.properties,
        datetime=single_datetime,
        cog_url=item.s3_filename,
        collection=item.collection,
        asset_name=item.asset_name,
        asset_roles=item.asset_roles,
        asset_media_type=item.asset_media_type,
    )


@generate_stac.register
def generate_stac_cmrevent(item: events.CmrEvent) -> pystac.Item:
    """
    Generate STAC Item from CMR granule
    """
    cmr_json = GranuleQuery().concept_id(item.granule_id).get(1)[0]

    return create_item(
        properties=cmr_json,
        datetime=str_to_datetime(cmr_json["time_start"]),
        cog_url=item.s3_filename,
        collection=item.collection,
        asset_name=item.asset_name,
        asset_roles=item.asset_roles,
        asset_media_type=item.asset_media_type,
    )
