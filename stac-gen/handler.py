from cmr import GranuleQuery
import json
import pystac
from pystac.utils import str_to_datetime
from shapely.geometry import shape


def try_int(x):
    try:
        return int(x)
    except ValueError:
        return x


def create_item(entry):
    bbox = [try_int(x) for x in entry["boxes"][0].split(" ")]
    dt = str_to_datetime(entry["updated"])

    minX, minY, maxX, maxY = bbox
    coordinates = [(minX, minY), (minX, maxY), (maxX, maxY), (maxX, minY), (minX, minY)]
    geom = {"type": "Polygon", "coordinates": [coordinates]}

    granule_id = entry["id"]

    props = {
        "coordinate_system": entry["coordinate_system"],
        "day_night_flag": entry["day_night_flag"],
    }

    item = pystac.Item(
        id=granule_id, geometry=geom, bbox=bbox, datetime=dt, properties=props
    )

    for link in entry["links"]:
        if ".he5" in link["href"]:
            name = link["title"] if "title" in link else link["href"]
            item.add_asset(
                name,
                pystac.Asset(
                    href=link["href"],
                    media_type="application/x-hdf5",
                    roles=["data"],
                    title="hdf image",
                ),
            )

    return item


def handler(event, context):
    """
    Lambda handler for STAC Collection Item generation
    """
    api = GranuleQuery()

    # Granule Id and concept Id refer to the same thing
    # Different terminology is used by different sections of CMR

    concept_id = event["granule_id"]
    cmr_json = api.concept_id(concept_id).get(1)

    stac_item = create_item(cmr_json[0])
    print("Created item...")

    return stac_item


if __name__ == "__main__":
    sample_event = {
        "collection": "OMNO2d",
        "href": "https://acdisc.gesdisc.eosdis.nasa.gov/data//Aura_OMI_Level3/OMNO2d.003/2022/OMI-Aura_L3-OMNO2d_2022m0111_v003-2022m0112t181633.he5",
        "granule_id": "G2199243759-GES_DISC",
    }

    handler(sample_event, {})
