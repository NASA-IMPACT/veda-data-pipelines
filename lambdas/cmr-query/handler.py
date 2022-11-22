import re
import json
import datetime as dt

from cmr import GranuleQuery


def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event["collection"]
    version = event["version"]

    temporal = event.get("temporal", ["1000-01-01T00:00:00Z", "3000-01-01T23:59:59Z"])
    startdate = dt.datetime.strptime(temporal[0], "%Y-%m-%dT%H:%M:%SZ")
    enddate = dt.datetime.strptime(temporal[1], "%Y-%m-%dT%H:%M:%SZ")
    print(f"Querying for {collection} granules from {startdate} to {enddate}")

    api = GranuleQuery(mode="https://cmr.maap-project.org/search/")
    granules = (
        api.short_name(collection)
        .version(version)
        .temporal(startdate, enddate)
        .bounding_box(*event.get("bounding_box", [-180, -90, 180, 90]))
        .get_all()
    )

    granules_to_insert = []
    for granule in granules:
        for link in granule["links"]:
            if event.get("mode") == "stac":
                if link["href"][-9:] == "stac.json" and link["href"][0:5] == "https":
                    granules_to_insert.append(link)
            else:
                if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/s3#":
                    href = link["href"]
                    file_obj = {
                        "collection": collection,
                        "s3_filename": href,
                        "granule_id": granule["id"],
                        "id": granule["id"],
                        "mode": event.get("mode"),
                    }
                    if event.get("include"):
                        pattern = re.compile(event["include"])
                        matched = pattern.match(href)
                        if matched:
                            granules_to_insert.append(file_obj)
                    else:
                        granules_to_insert.append(file_obj)

    print(f"Returning {len(granules_to_insert)} granules to insert")
    print(json.dumps(granules_to_insert[0], indent=2))
    return {"cogify": event.get("cogify", False), "objects": granules_to_insert}


if __name__ == "__main__":
    sample_event = {
        "mode": "cmr",
        "collection": "ABLVIS1B",
        "version": "001"
    }
    handler(sample_event, {})
