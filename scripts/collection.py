import os
import glob
import json
import boto3

from .utils import args_handler, data_files, DATA_PATH, SUBMIT_STAC_FUNCTION_NAME

collections_path = os.path.join(DATA_PATH, 'collections')

lambda_client = boto3.client('lambda')

def insert_collections(files):
    print("Inserting collections:")
    for file in files:
        print(file)
        collections = json.load(open(file))
        if type(collections) != list:
            collections = [collections]
        for collection in collections:
            content = json.dumps({
                "stac_item": collection,
                "type": "collections"
            })
            response = lambda_client.invoke(
                FunctionName=SUBMIT_STAC_FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=content
            )
            print(response)
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                print(f'Error inserting collection {file}')
                print(response.get('Payload'))

@args_handler
def insert(collections):
    files = data_files(collections, collections_path)
    insert_collections(files)

@args_handler
def delete(collections):
    print("Function not implemented")

@args_handler
def update(collections):
    print("Function not implemented")

if __name__=="__main__":
    insert()
