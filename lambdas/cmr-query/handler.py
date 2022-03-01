import datetime as dt
from cmr import GranuleQuery
import re
import json
import os
import boto3



def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event["collection"]
    version = event["version"]

    enddate = dt.datetime.strptime(event['end_date'], '%Y-%m-%d %H:%M:%S') if 'end_date' in event else dt.datetime.now()
    startdate = enddate - dt.timedelta(hours=event["hours"])
    print(f"Querying for {collection} granules from {startdate} to {enddate}")

    api = GranuleQuery()
    granules = (
        api.short_name(collection)
        .version(version)
        .temporal(startdate, enddate)
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

    print(f"Returning urls {urls}")
    return urls


if __name__ == "__main__":
        "hours": 4,
        "end_date": "2021-07-29 05:00:00",
        "mode": "stac",
        "queue_messages": True,
        "collection": "HLSS30",
        "version": "2.0",
        "include": "^.+he5$",
    }
    handler(sample_event, {})
