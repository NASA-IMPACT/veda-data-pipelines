import os
import re

import datetime as dt

import boto3

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
    print(granules[0])
    for granule in granules:
        for link in granule["links"]:
            if event.get('mode') == 'stac':
                if link["href"][-9:] == "stac.json" and link["href"][0:5] == "https":
                    urls.append(link)
            else:
                if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#":
                    href = link["href"]
                    file_obj = {
                        **event,
                        "collection": collection,
                        "href": href,
                        "granule_id": granule["id"],
                        "id": granule["id"],
                        "upload": True,
                        "start_datetime": granule["time_start"],
                        "end_datetime": granule["time_end"],
                    }
                    if event["include"]:
                        pattern = re.compile(event["include"])
                        matched = pattern.match(href)
                        if matched:
                            urls.append(file_obj)
                    else:
                        urls.append(file_obj)
    if event["queue_messages"]:
        client = boto3.client("sqs")
        QUEUE_URL = os.environ["QUEUE_URL"]
        for item_url in urls:
            # TODO: send item_url instead
            client.send_message(QueueUrl=QUEUE_URL, MessageBody=item_url['href'])

    print(f"Returning {len(urls)} urls")
    print(urls[0])
    return urls


if __name__ == "__main__":
    sample_event = {
        # "mode": "stac",
        "queue_messages": False,
        "collection": "IS2SITMOGR4",
        "version": "1",
        "include": "^.+nc$",
        "temporal": ["2018-01-21T00:00:00Z","2021-05-20T23:59:59Z"],
        "bounding_box": [-180, -90, 180, 90]
    }
    handler(sample_event, {})
