import argparse
import datetime as dt
import json
from cmr import GranuleQuery
import re

parser = argparse.ArgumentParser(description="Query CMR for recent files from a given collection")
parser.add_argument("-d", "--days", help="How many days past to query", default=7)
parser.add_argument('-c', '--collection', help='Collection short name', default="OMNO2d")
parser.add_argument('--include', help='only inlude links which match this regex')
args = parser.parse_args()
collection = args.collection

enddate = dt.datetime.now()
startdate = enddate - dt.timedelta(days=args.days)
print(f"Querying for {collection} granules from {startdate} to {enddate}")

api = GranuleQuery()
granules = api.short_name(collection).temporal(startdate, enddate).get(5)

granule = granules[0]
urls = []
for link in granule['links']:
    if link['rel'] == 'http://esipfed.org/ns/fedsearch/1.1/data#':
        href = link['href']
        if args.include:
            pattern = re.compile(args.include)
            matched = pattern.match(href)
            if matched:
                urls.append(href)
        else:
            urls.append(href)

print(urls)
c