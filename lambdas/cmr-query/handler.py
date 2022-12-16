import os
import re
import json
import datetime as dt

import requests

def get_cmr_granules_endpoint(event):
    default_cmr_api_url = "https://cmr.earthdata.nasa.gov"
    cmr_api_url = event.get('cmr_api_url', os.environ.get('CMR_API_URL', default_cmr_api_url))
    cmr_granules_search_url = f"{cmr_api_url}/search/granules.json"
    return cmr_granules_search_url

def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event["collection"]
    version = event["version"]

    temporal = event.get("temporal", ["1000-01-01T00:00:00Z", "3000-01-01T23:59:59Z"])
    page = event.get('start_after', 1)
    limit = event.get('limit', 100)

    search_endpoint = f"{get_cmr_granules_endpoint(event)}?short_name={collection}&version={version}" + \
      f"&temporal[]={temporal[0]},{temporal[1]}&page_size={limit}"
    search_endpoint = f"{search_endpoint}&page_num={page}"
    print(f"Discovering data from {search_endpoint}")
    response = requests.get(search_endpoint)

    if response.status_code != 200:
        print(f"Got an error from CMR: {response.status_code} - {response.text}")
        return
    else:
        hits = response.headers['CMR-Hits']
        print(f"Got {hits} from CMR")
        granules = json.loads(response.text)['feed']['entry']
        print(f"Got {len(granules)} to insert")
        # Decide if we should continue after this page
        # Start paging if there are more hits than the limit
        # Stop paging when there are no more results to return
        if len(granules) > 0 and int(hits) > limit*page:
            print(f"Got {int(hits)} which is greater than {limit*page}")
            page += 1
            event['start_after'] = page
            print(f"Returning next page {event.get('start_after')}")
        else:
            event.pop('start_after', None)

    granules_to_insert = []
    for granule in granules:
        file_obj = {}
        for link in granule["links"]:
            if event.get("mode") == "stac":
                if link["href"][-9:] == "stac.json" and link["href"][0:5] == "https":
                    granules_to_insert.append(link)
            else:
                if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/s3#" or link["rel"] == event.get('link_rel'):
                    href = link["href"]
                    file_obj = {
                        "collection": collection,
                        "remote_fileurl": href,
                        "granule_id": granule["id"],
                        "id": granule["id"],
                        "mode": event.get("mode"),
                        "test_links": event.get("test_links"),
                        "reverse_coords": event.get("reverse_coords")
                    }
                    # don't overwrite the fileurl if it's already been discovered.
                    for key, value in event.items():
                        if 'asset' in key:
                            file_obj[key] = value
        granules_to_insert.append(file_obj)

    # Useful for testing locally with build-stac/handler.py
    print(json.dumps(granules_to_insert[0], indent=2))
    return_obj = {
        **event,
        "cogify": event.get("cogify", False),
        "objects": granules_to_insert
    }
    return return_obj


if __name__ == "__main__":
    sample_event = {
        "queue_messages": "true",
        "collection": "GEDI02_B",
        "version": "002",
        "discovery": "cmr",
        "temporal": ["2021-11-01T00:00:00Z", "2021-12-31T23:59:59Z"],
        "mode": "cmr",
        "asset_name": "data",
        "asset_roles": ["data"],
        "asset_media_type": "application/x-hdf5"
    }

    handler(sample_event, {})
