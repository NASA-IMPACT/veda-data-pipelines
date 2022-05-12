import os
import json
import boto3

from .utils import args_handler, data_files, DATA_PATH

items_path = os.path.join(DATA_PATH, 'events')
sf_client = boto3.client('stepfunctions')

def insert_items(files):
    print("Inserting collections:")
    for filename in files:
        print(filename)
        events = json.load(open(filename))
        if type(events) != list:
            events = [events]
        for event in events:
            response = sf_client.start_execution(
                stateMachineArn=f"arn:aws:states:us-east-1:853558080719:stateMachine:delta-simple-ingest-{os.environ.get('ENV', 'dev')}-stepfunction-discover",
                input=json.dumps(event)
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
