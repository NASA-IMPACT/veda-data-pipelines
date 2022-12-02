import re
import json
import datetime as dt

import requests

def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event["collection"]
    version = event["version"]

    temporal = event.get("temporal", ["1000-01-01T00:00:00Z", "3000-01-01T23:59:59Z"])
    startdate = dt.datetime.strptime(temporal[0], "%Y-%m-%dT%H:%M:%SZ")
    enddate = dt.datetime.strptime(temporal[1], "%Y-%m-%dT%H:%M:%SZ")
    page = event.get('start_after')
    limit = event.get('limit', 100)

    cmr_api_url = f"https://cmr.maap-project.org/search/granules.json"
    search_endpoint = f"{cmr_api_url}?short_name={collection}&version={version}" + \
      f"&temporal[]={temporal[0]},{temporal[1]}&page_size={limit}"
    print(f"Discovering data from {search_endpoint}")
    if page:
        search_endpoint = f"{search_endpoint}&page_num={page}"
        page +=1
    # SEarch after is throwing 500 error in CMR
    # headers = {'CMR-Search-After': str(event.get('search_after'))}
    response = requests.get(search_endpoint)
    if response.status_code != 200:
        print(f"Got an error from CMR: {response.status_code} - {response.text}")
        return
    else:
        hits = response.headers['CMR-Hits']
        print(f"Got {hits} from CMR")
        granules = json.loads(response.text)['feed']['entry']
    granules_to_insert = []
    for granule in granules:
        file_obj = {}
        for link in granule["links"]:
            if event.get("mode") == "stac":
                if link["href"][-9:] == "stac.json" and link["href"][0:5] == "https":
                    granules_to_insert.append(link)
            else:
                if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/s3#" or link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#":
                    href = link["href"]
                    file_obj = {
                        "collection": collection,
                        "remote_fileurl": href,
                        "granule_id": granule["id"],
                        "id": granule["id"],
                        "mode": event.get("mode")
                    }
                    for key, value in event.items():
                        if 'asset' in key:
                            file_obj[key] = value
        granules_to_insert.append(file_obj)



    print(f"Returning {len(granules_to_insert)} granules to insert")
    # Useful for testing locally with build-stac/handler.py
    # print(json.dumps(granules_to_insert[0], indent=2))
    return_obj = {
        **event,
        "cogify": event.get("cogify", False),
        "objects": granules_to_insert
    }
    # print(json.dumps(granules_to_insert[0], indent=2))
    if len(granules_to_insert) > 0:
        return_obj['start_after'] = page or 2
        print(f"returning next page {return_obj['start_after']}")
    else:
        return_obj.pop('start_after')
    return return_obj


if __name__ == "__main__":
    sample_event = {
        "queue_messages": "true",
        "collection": "AFRISAR_DLR",
        "temporal": ["2021-01-01T00:00:00Z", "2021-12-31T23:59:59Z"],
        "version": "1",
        "discovery": "cmr",
        "asset_name": "data",
        "asset_roles": ["data"],
        "start_after": 1
    }
    handler(sample_event, {})
