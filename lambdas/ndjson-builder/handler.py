import asyncio
import json
import os
from typing import Dict, List
from urllib.parse import urlparse
from uuid import uuid4

import aiohttp
import boto3
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from smart_open import open

"""
Code adapted from https://github.com/NASA-IMPACT/cmr-pgstac-loader/blob/main/cdk/app.py @author @sharkinsspatial
"""


def update_href(asset: Dict):
    """Update asset protected http endpoint to the internal S3 endpoint"""
    href = asset["href"]
    url_components = urlparse(href)
    hostname = url_components.hostname
    scheme = url_components.scheme
    if url_components.path.split("/")[1] == "lp-prod-protected":
        s3_href = href.replace(f"{scheme}://{hostname}/", "s3://")
        updated_asset = asset.copy()
        updated_asset["href"] = s3_href
    else:
        updated_asset = asset
    return updated_asset


async def stream_stac_items(urls: List[str], key: str, collection: str = None):
    with open(key, "w") as f:
        async with aiohttp.ClientSession() as session:
            for url in urls:
                async with session.get(url) as resp:
                    stac = await resp.json()
                    url_components = urlparse(url)
                    stac["collection"] = collection if collection else url_components.path.split("/")[2].split(".")[0]
                    assets = {k: update_href(v) for (k, v) in stac["assets"].items()}
                    stac["assets"] = assets
                    f.write(json.dumps(stac) + "\n")


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context):
    BUCKET = os.environ["BUCKET"]
    QUEUE_URL = os.environ["QUEUE_URL"]
    COLLECTION = os.environ["COLLECTION"]
    print(event)
    item_urls = [record.body for record in event.records]
    print(event)
    print(item_urls)
    file_id = str(uuid4())
    key = f"s3://{BUCKET}/{file_id}.ndjson"
    print(key)
    asyncio.run(stream_stac_items(item_urls, key, COLLECTION))
    client = boto3.client("sqs")
    client.send_message(QueueUrl=QUEUE_URL, MessageBody=key)
