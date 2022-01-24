from cmr import GranuleQuery
import os
import json
import pystac
from pystac.utils import str_to_datetime
from shapely.geometry import shape
from pypgstac import pypgstac
from rio_stac.stac import bbox_to_geom, create_stac_item

STAC_DB_HOST = os.environ.get('STAC_DB_HOST')
STAC_DB_USER = os.environ.get('STAC_DB_USER')
STAC_DB_PASSWORD = os.environ.get('STAC_DB_PASSWORD')

def create_item(cmr, cog_url, collection):

    assets = {}

    for link in cmr["links"]:
        if ".he5" in link["href"]:
            name = link["title"] if "title" in link else link["href"]
            assets[name] = pystac.Asset(
                href=link["href"],
                media_type="application/x-hdf5",
                roles=["data"],
                title="hdf image",
            )
    # TODO placeholder
    assets['cog'] = pystac.Asset(
        href=cog_url,
        media_type='image/tiff; application=geotiff',
        roles=["data"],
        title="COG"
    )


    dt = str_to_datetime(cmr["time_start"])

    try:
        rstac = create_stac_item(
            source=cog_url,
            collection=collection,
            input_datetime=dt,
            properties=cmr,
            with_proj=True,
            with_raster=True,
            assets=assets
        )
        print(rstac.to_dict())
    except:
        return f"failed {cmr['id']}"

    return rstac


def handler(event, context):
    """
    Lambda handler for STAC Collection Item generation
    """
    api = GranuleQuery()

    # Granule Id and concept Id refer to the same thing
    # Different terminology is used by different sections of CMR

    concept_id = event["granule_id"]
    cmr_json = api.concept_id(concept_id).get(1)

    cog = event["s3_filename"]
    collection = event["collection"]

    stac_item = create_item(cmr=cmr_json[0], cog_url=cog, collection=collection)

    with open("temp.json", "w+") as f:
        f.write(json.dumps(stac_item.to_dict()))

    pypgstac.load(
        table="items",
        file="temp.json",
        dsn=f"postgres://{STAC_DB_USER}:{STAC_DB_PASSWORD}@{STAC_DB_HOST}/postgis",
        method="insert_ignore",  # use insert_ignore to avoid overwritting existing items
    )

    print("Created item...")

if __name__ == "__main__":
    sample_event = {
        "collection": "OMNO2d",
        "href": "https://acdisc.gesdisc.eosdis.nasa.gov/data//Aura_OMI_Level3/OMNO2d.003/2022/OMI-Aura_L3-OMNO2d_2022m0111_v003-2022m0112t181633.he5",
        "s3_filename": "s3://climatedashboard-data/OMDOAO3e/OMI-Aura_L3-OMDOAO3e_2022m0105_v003-2022m0107t023328.he5.tif",
        "granule_id": "G2199243759-GES_DISC",
    }

    handler(sample_event, {})
