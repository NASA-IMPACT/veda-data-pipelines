import datetime as dt
from cmr import GranuleQuery
import re

def handler(event, context):
    """
    Lambda handler for the NetCDF ingestion pipeline
    """
    collection = event['collection']

    enddate = dt.datetime.now()
    startdate = enddate - dt.timedelta(days=event['days'])
    print(f"Querying for {collection} granules from {startdate} to {enddate}")

    api = GranuleQuery()
    granules = api.short_name(collection).temporal(startdate, enddate).get(5)

    granule = granules[0]
    urls = []
    for link in granule['links']:
        if link['rel'] == 'http://esipfed.org/ns/fedsearch/1.1/data#':
            href = link['href']
            if event['include']:
                pattern = re.compile(event['include'])
                matched = pattern.match(href)
                if matched:
                    urls.append(href)
            else:
                urls.append(href)
    print(f"Returning urls {urls}")
    return urls

if __name__ == '__main__':
    sample_event = {
        "collection": "OMNO2d",
        "days": 7,
        "include": "^.+he5$"
    }    
    handler(sample_event, {})
