import json
import boto3

from dotenv import load_dotenv
from .utils import args_handler, get_items, get_sf_ingestion_arn


def insert_items(files):
    print("Inserting items:")
    for filename in files:
        print(filename)
        events = json.load(open(filename))
        if type(events) != list:
            events = [events]

        sf_client = boto3.client("stepfunctions")
        sf_arn = get_sf_ingestion_arn()
        for event in events:
            response = sf_client.start_execution(
                stateMachineArn=sf_arn, input=json.dumps(event)
            )
            print(response)


@args_handler
def insert(items):
    load_dotenv()
    files = get_items(items)
    insert_items(files)


def update(items):
    print("Function not implemented")


def delete(items):
    print("Function not implemented")
