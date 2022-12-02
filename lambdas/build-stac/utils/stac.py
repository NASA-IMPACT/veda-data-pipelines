import os
import json
import geojson
from pathlib import Path
from functools import singledispatch

import pystac
import rasterio

from cmr import GranuleQuery
from pystac.utils import str_to_datetime
from rio_stac import stac
from rasterio.session import AWSSession

from . import regex, events, role


def create_item(
    id,
    properties,
    datetime,
    cog_url,
    collection,
    bbox,
    geometry,
    assets=None,
    asset_name=None,
    asset_roles=None,
    asset_media_type=None,
) -> pystac.Item:
    """
    Function to create a stac item from a COG using rio_stac
    """

    def create_stac_item():
        try:
            return stac.create_stac_item(
                id=Path(cog_url).stem,
                source=cog_url,
                collection=collection,
                input_datetime=datetime,
                properties=properties,
                with_proj=True,
                with_raster=True,
                assets=assets,
                asset_name=asset_name or "cog_default",
                asset_roles=asset_roles or ["data", "layer"],
                asset_media_type=(
                    asset_media_type
                    or "image/tiff; application=geotiff; profile=cloud-optimized"
                ),
            )
        except Exception as e:
            print(f"Caught exception {e}")
            if 'not recognized as a supported file format' in str(e):
                stac_item = pystac.Item(
                    id=Path(cog_url).stem,
                    geometry=geometry,
                    properties=properties,
                    href=cog_url,
                    datetime=datetime,
                    collection=collection,
                    bbox=bbox
                )
                stac_item.assets = assets
                return stac_item
            else:
                raise

    rasterio_kwargs = {}
    if role_arn := os.environ.get("DATA_MANAGEMENT_ROLE_ARN"):
        creds = role.assume_role(role_arn, "veda-data-pipelines_build-stac")
        rasterio_kwargs["session"] = AWSSession(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds['SessionToken'],
        )

    with rasterio.Env(
        session=rasterio_kwargs.get("session"),
        options={
            **rasterio_kwargs,
            "GDAL_MAX_DATASET_POOL_SIZE": 1024,
            "GDAL_DISABLE_READDIR_ON_OPEN": False,
            "GDAL_CACHEMAX": 1024000000,
            "GDAL_HTTP_MAX_RETRY": 4,
            "GDAL_HTTP_RETRY_DELAY": 1,
        },
    ):
        return create_stac_item()


@singledispatch
def generate_stac(item) -> pystac.Item:
    raise Exception(f"Unsupport event type: {type(item)=}, {item=}")


@generate_stac.register
def generate_stac_regexevent(item: events.RegexEvent) -> pystac.Item:
    """
    Generate STAC item from user provided datetime range or regex & filename
    """
    if item.start_datetime and item.end_datetime:
        start_datetime = item.start_datetime
        end_datetime = item.end_datetime
        single_datetime = None
    elif single_datetime := item.single_datetime:
        start_datetime = end_datetime = None
        single_datetime = single_datetime
    else:
        start_datetime, end_datetime, single_datetime = regex.extract_dates(
            item.remote_fileurl, item.datetime_range
        )
    properties = item.properties or {}
    if start_datetime and end_datetime:
        properties["start_datetime"] = start_datetime.isoformat()
        properties["end_datetime"] = end_datetime.isoformat()
        single_datetime = None

    return create_item(
        id=item.item_id(),
        properties=properties,
        datetime=single_datetime,
        cog_url=item.remote_fileurl,
        collection=item.collection,
        asset_name=item.asset_name,
        asset_roles=item.asset_roles,
        asset_media_type=item.asset_media_type,
    )


def pairwise(iterable):
    # "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)

def get_bbox(coord_list):
     box = []
     for i in (0,1):
         res = sorted(coord_list, key=lambda x:x[i])
         box.append((res[0][i],res[-1][i]))
     ret = [box[0][0], box[1][0], box[0][1], box[1][1]]
     return ret

def generate_geometry_from_cmr(cmr_json):
    if cmr_json.get('polygons'):
        str_coords = cmr_json['polygons'][0][0].split()
        polygon_coords = [(float(x), float(y)) for x,y in pairwise(str_coords)]
        return {
            "coordinates": [polygon_coords],
            "type": "Polygon"
        }
    else:
        return None

def get_assets_from_cmr(cmr_json):
    """
    each asset has a key and the values within should be
    roles, href, title, description, type. Only href is required.
    """
    assets = {}
    links = cmr_json['links']
    for link in links:
        if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#":
            extension = os.path.splitext(link['href'])[-1].replace('.', '')
            role = 'data'
            if extension == 'prj':
                role = 'metadata'
            assets[extension] = pystac.Asset(
                roles=[role],
                href=link.get('href'),
                media_type=link.get('type')
            )
    return assets

@generate_stac.register
def generate_stac_cmrevent(item: events.CmrEvent) -> pystac.Item:
    """
    Generate STAC Item from CMR granule
    """
    cmr_json = GranuleQuery(mode="https://cmr.maap-project.org/search/").concept_id(item.granule_id).get(1)[0]
    cmr_json['concept_id'] = cmr_json.pop('id')
    geometry = generate_geometry_from_cmr(cmr_json)
    if geometry:
        bbox = get_bbox(list(geojson.utils.coords(geometry['coordinates'])))
    else:
        bbox = None
    assets = get_assets_from_cmr(cmr_json)

    return create_item(
        id=item.item_id(),
        properties=cmr_json,
        datetime=str_to_datetime(cmr_json["time_start"]),
        cog_url=item.remote_fileurl,
        collection=item.collection,
        asset_name=item.asset_name,
        asset_roles=item.asset_roles,
        asset_media_type=item.asset_media_type,
        assets=assets,
        bbox=bbox,
        geometry=geometry
    )