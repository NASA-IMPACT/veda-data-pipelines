import datetime as dt
from cmr import GranuleQuery
import re
import os
import boto3


def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event["collection"]
    version = event["version"]

    startdate = dt.datetime.strptime(event["temporal"][0], '%Y-%m-%dT%H:%M:%SZ')
    enddate = dt.datetime.strptime(event["temporal"][1], '%Y-%m-%dT%H:%M:%SZ')
    print(f"Querying for {collection} granules from {startdate} to {enddate}")

    api = GranuleQuery()
    granules = (
        api.short_name(collection)
        .version(version)
        .temporal(startdate, enddate)
        .bounding_box(*event["bounding_box"])
        .get_all()
    )

    urls = []
    for granule in granules:
        for link in granule["links"]:
            if event['mode'] == 'stac':
                if link["href"][-9:] == "stac.json" and link["href"][0:5] == "https":
                    urls.append(link)
            else:
                if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#":
                    href = link["href"]
                    file_obj = {
                        "collection": collection,
                        "href": href,
                        "granule_id": granule["id"],
                        "upload": True,
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
            client.send_message(QueueUrl=QUEUE_URL, MessageBody=item_url['href'])

    print(f"Returning {len(urls)} urls")
    return urls


if __name__ == "__main__":
    sample_event = {
        "mode": "stac",
        "queue_messages": False,
        "collection": "HLSS30",
        "version": "2.0",
        "include": "^.+he5$",
        "temporal": ["2018-01-21T00:00:00Z","2018-03-20T23:59:59Z"],
        "bounding_box": [-67.2716765, 17.9121390, -65.5747876, 18.5156946]
    }
    handler(sample_event, {})
