import os
import glob
import json
import boto3

from .utils import args_handler


collections_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'collections')
lambda_client = boto3.client('lambda')

def collection_files(collections, collections_path):
    files = []
    for collection in collections:
        files.extend(glob.glob(os.path.join(collections_path,  f'{collection}*.json')))
    return files

def insert_collections(files):
    print("Inserting collections:")
    for file in files:
        print(file)
        content = json.dumps({
            "stac_item": json.load(open(file)),
            "type": "collections"
        })
        print(f"{os.environ.get('APP_NAME')}-{os.environ.get('ENV')}-lambda-pgstac-loader-fn")
        response = lambda_client.invoke(
            FunctionName=f"{os.environ.get('APP_NAME')}-{os.environ.get('ENV')}-lambda-pgstac-loader-fn",
            InvocationType='RequestResponse',
            Payload=content
        )
        print(response)
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print(f'Error inserting collection {file}')
            print(response.get('Payload'))

@args_handler
def insert(collections):
    files = collection_files(collections, collections_path)
    insert_collections(files)

@args_handler
def delete(collections):
    print("Function not implemented")

@args_handler
def update(collections):
    print("Function not implemented")

if __name__=="__main__":
    insert()
