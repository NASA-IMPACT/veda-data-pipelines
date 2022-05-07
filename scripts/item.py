import os
import json
import boto3
import time

from .utils import args_handler, data_files

items_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'events')
sf_client = boto3.client('stepfunctions')

def insert_items(files):
    print("Inserting collections:")
    for filename in files:
        print(filename)
        events = json.load(open(filename))
        for event in events:
            time.sleep(5)
            response = sf_client.start_execution(
                stateMachineArn="arn:aws:states:us-east-1:853558080719:stateMachine:delta-simple-ingest-dev-stepfunction-discover",
                input=json.dumps(event)
            )
            print(response)

@args_handler
def insert(items):
    files = data_files(items, items_path)
    insert_items(files)

def update():
    print("Function not implemented")

def delete():
    print("Function not implemented")
