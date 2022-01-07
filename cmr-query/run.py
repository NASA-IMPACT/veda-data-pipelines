import argparse
import datetime as dt
import json
from cmr import GranuleQuery
import re

def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event.collection

    enddate = dt.datetime.now()
    startdate = enddate - dt.timedelta(days=event.days)
    print(f"Querying for {collection} granules from {startdate} to {enddate}")

    api = GranuleQuery()
    granules = api.short_name(collection).temporal(startdate, enddate).get(5)

    granule = granules[0]
    urls = []
    for link in granule['links']:
        if link['rel'] == 'http://esipfed.org/ns/fedsearch/1.1/data#':
            href = link['href']
            if event.include:
                pattern = re.compile(event.include)
                matched = pattern.match(href)
                if matched:
                    urls.append(href)
            else:
                urls.append(href)

    return urls

parser = argparse.ArgumentParser(description="Query CMR for recent files from a given collection")
parser.add_argument("-d", "--days", help="How many days past to query", type=int, default=7)
parser.add_argument('-c', '--collection', help='Collection short name', default="OMNO2d")
parser.add_argument('--include', help='only inlude links which match this regex')
event = parser.parse_args()
print(handler(event, {}))