import re

import datetime as dt

from cmr import GranuleQuery


def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event["collection"]
    version = event["version"]

    temporal = event.get("temporal", ["1000-01-01T00:00:00Z","3000-01-01T23:59:59Z"])
    startdate = dt.datetime.strptime(temporal[0], '%Y-%m-%dT%H:%M:%SZ')
    enddate = dt.datetime.strptime(temporal[1], '%Y-%m-%dT%H:%M:%SZ')
    print(f"Querying for {collection} granules from {startdate} to {enddate}")

    api = GranuleQuery()
    granules = (
        api.short_name(collection)
        .version(version)
        .temporal(startdate, enddate)
        .bounding_box(*event.get("bounding_box", [-180, -90, 180, 90]))
        .get_all()
    )

    urls = []
    for granule in granules:
        for link in granule["links"]:
            if event.get('mode') == 'stac':
                if link["href"][-9:] == "stac.json" and link["href"][0:5] == "https":
                    urls.append(link)
            else:
                if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#":
                    href = link["href"]
                    file_obj = {
                        "collection": collection,
                        "href": href,
                        "granule_id": granule["id"],
                        "id": granule["id"],
                        "mode": event.get('mode'),
                        # "start_datetime": granule["time_start"],
                        # "end_datetime": granule["time_end"]
                    }
                    if event["include"]:
                        pattern = re.compile(event["include"])
                        matched = pattern.match(href)
                        if matched:
                            urls.append(file_obj)
                    else:
                        urls.append(file_obj)

    print(f"Returning {len(urls)} urls")
    return {
        "cogify": event.get("cogify", False),
        "objects": urls
    }


if __name__ == "__main__":
    sample_event = {
        # "mode": "stac",
        "collection": "IS2SITMOGR4",
        "version": "1",
        "include": "^.+nc$",
        "temporal": ["2018-01-21T00:00:00Z","2018-04-20T23:59:59Z"],
        "bounding_box": [-180, -90, 180, 90]
    }
    handler(sample_event, {})
