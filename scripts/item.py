import os
import boto3

import orjson

from .utils import args_handler, data_files, DATA_PATH, INGESTION_STEP_MACHINE_ARN

items_path = os.path.join(DATA_PATH, "step_function_inputs")
sf_client = boto3.client("stepfunctions")


def insert_items(files):
    print("Inserting items:")
    for filename in files:
        print(filename)
        events = orjson.load(open(filename))
        if type(events) != list:
            events = [events]
        for event in events:
            response = sf_client.start_execution(
                stateMachineArn=INGESTION_STEP_MACHINE_ARN,
                input=orjson.dumps(event).decode("utf8")
            )
            print(response)


@args_handler
def insert(items):
    files = data_files(items, items_path)
    insert_items(files)


def update(items):
    print("Function not implemented")


def delete(items):
    print("Function not implemented")
