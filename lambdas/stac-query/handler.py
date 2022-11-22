import json
import re
import requests
import datetime as dt
import os

def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event["collection"]
    version = event["version"]

    temporal = event.get("temporal", ["1000-01-01T00:00:00Z", "3000-01-01T23:59:59Z"])
    startdate = dt.datetime.strptime(temporal[0], "%Y-%m-%dT%H:%M:%SZ")
    enddate = dt.datetime.strptime(temporal[1], "%Y-%m-%dT%H:%M:%SZ")
    print(f"Querying for {collection} items from {startdate} to {enddate}")
    STAC_API_ENDPOINT = event.get('STAC_API_ENDPOINT') or os.environ.get("STAC_API_ENDPOINT");
    PROVIDER = event.get('provider') or os.environ.get("STAC_PROVIDER");
    url = f"{STAC_API_ENDPOINT}/{PROVIDER}/collections/{collection}/items"
    response = requests.get(url)
    items = []
    if response.status_code == 200:
        items = json.loads(response.text)['features']
    else:
        print(f"Got {response.status_code} status from {url}")

    items_to_insert = []
    for item in items:
        for link in item["links"]:
            if event.get("mode") == "stac":
                if link["rel"] == "self":
                    # hopefully temporary workaround for CMR STAC Proxy
                    href = link['href'].replace('/stac', '/dev/stac')
                    item_to_insert = {
                        "collection": collection,
                        "href": href,
                        "mode": event.get("mode")
                    }                    
                    items_to_insert.append(item_to_insert)
    print(f"Returning {len(items_to_insert)} items")
    return {"cogify": event.get("cogify", False), "objects": items_to_insert}


if __name__ == "__main__":
    sample_event = {
        "mode": "stac",
        "collection": "ABLVIS1B.v001",
        "version": "001"
    }
    handler(sample_event, {})
