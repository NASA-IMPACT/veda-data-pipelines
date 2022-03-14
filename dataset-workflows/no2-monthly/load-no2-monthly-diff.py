# python3.8
import os
import json
import datetime
import concurrent.futures
from typing import Union

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

import boto3
import base64
from botocore.exceptions import ClientError
from mypy_boto3_s3.service_resource import S3ServiceResource
# tqdm provides progress bars
from tqdm import tqdm

import pystac
from pypgstac import pypgstac
import rio_stac

def get_secret(secret_name:str, profile_name:str=None) -> None:
    """Retrieve secrets from AWS Secrets Manager

    Args:
        secret_name (str): name of aws secrets manager secret containing database connection secrets
        profile_name (str, optional): optional name of aws profile for use in debugger only

    Returns:
        secrets (dict): decrypted secrets in dict
    """

    # Create a Secrets Manager client
    if profile_name:
        session = boto3.session.Session(profile_name=profile_name)
    else:
        session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            raise e
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])
        else:
            return json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))
            
def get_dsn_string(secret:dict) -> str:
    """Form database connection string from a dictionary of connection secrets

    Args:
        secret (dict): dictionary containing connection secrets including username, database name, host, and password

    Returns:
        dsn (str): full database data source name
    """
    try:
        return f"postgres://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['dbname']}"
    except Exception as e:
        raise e

def create_stac_item(obj: S3ServiceResource.ObjectSummary, collection_id: str) -> Union[pystac.Item, str]:
    """
    Generates a STAC Item object from a COG in S3
    
    :param obj: The S3 object summary of the file for which to create 
                a STAC Item
    :param collection_id: str STAC Item's parent Collection id         
    :returns: STAC Item
    :returns: str if STAC Item generation failed
    :raises Exception: if unable to extract variable name, date or SSP from filename
    """
    
    filename = obj.key.split("/")[-1]
    date = filename.split("_")[3]
    # Strip extensions from filename for id
    item_id = filename.replace(".nc.tif", f"-{collection_id}")
    
    try: 
        item = rio_stac.stac.create_stac_item(
          id = item_id,
          source = f"s3://{obj.bucket_name}/{obj.key}", 
          collection = collection_id, 
          input_datetime = datetime.datetime.strptime(date, "%Y%m"),
          with_proj = True,
          with_raster = True,
          asset_name = "cog_default",
          asset_roles = ["data", "layer"],
          asset_media_type = "image/tiff; application=geotiff; profile=cloud-optimized",
        ) 

        # Pystac Item.validate() will raise exception for invalid item
        item.validate()
        return item

    except Exception as e:
      print(e)
      return f"FAILED:{obj.key}"

def update_collection_summaries(cursor, collection_id: str) -> None:
  """Update summaries object in pgstac for all items in collection"""
  cursor.execute(
    sql.SQL("""
        SELECT update_default_summaries(id)
        FROM collections
        WHERE collections.id = (%s);
        """), (collection["id"],)
  )

collection={
    "id": "no2-monthly-diff",
    "type": "Collection",
    "title": "NO\u2082 Monthly (Diff)",
    "description": "This layer shows changes in nitrogen dioxide (NO₂) levels. Redder colors indicate increases in NO₂. Bluer colors indicate lower levels of NO₂. Missing pixels indicate areas of no data most likely associated with cloud cover or snow.",
    "stac_version": "1.0.0",
    "license": "MIT",
    "links": [],
    "extent": {
      "spatial": {
        "bbox": [
          [
            -180,
            -90,
            180,
            90
          ]
        ]
      },
      "temporal": {
        "interval": [
          [
            "2015-01-01T00:00:00Z",
            "2022-01-01T00:00:00Z"
          ]
        ]
      }
    },
    "item_assets": {
      "cog_default": {
        "type": "image/tiff; application=geotiff; profile=cloud-optimized",
        "title": "Default COG Layer",
        "description": "Cloud optimized default layer to display on map",
        "roles": ["data", "layer"]
      }
    },
    "dashboard:is_periodic": True,
    "dashboard:time_density": "month",
    "stac_extensions": ["https://stac-extensions.github.io/item-assets/v1.0.0/schema.json"]
  }

# GDAL attempts to list the directory when it opens a file, in order to 
# find "sidecar" files. This setting tells GDAL to assume the directory
# is empty when opening a file, saving both on S3 LIST costs and 
# runtime. See: https://github.com/OSGeo/gdal/issues/909
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"

# Name or ARN of secret containing connection info for target environment
secret_name = "my-aws-secret-name-or-arn"

# Name of AWS profile or none to use default profile
profile_name = "my-profile-name" 

# use `profile_name: str` param `Session()` or default AWS profile to ensure 
# correct access
BUCKET = boto3.Session().resource("s3").Bucket("s3-bucket-name")

# S3 prefix for searching 
prefix = "OMNO2d_HRMDifference"
tmp_collection_file = "no2-diff-collection-nd.json"
tmp_items_file = "no2-diff-items-nd.json"
dry_run = True # Just generate ndjson files and save to review in a dry run or publish to pgstac if false

if __name__ == "__main__":

    # Load connection info
    con_secrets = get_secret(secret_name, profile_name=profile_name)
    dsn = get_dsn_string(
      con_secrets
    )

    # Load collection into pgstac
    with open(tmp_collection_file, "w") as f:
      f.write(f"{json.dumps(collection)}\n")
      print(f"temporary collection file written to {tmp_collection_file} {os.path.exists(tmp_collection_file)}")

    if not dry_run:
      # Load collection into pgstac and remove temporary file 
      pypgstac.load(
        table="collections",
        file=tmp_collection_file,
        dsn=dsn,
        method="insert_ignore", # use insert_ignore to avoid overwritting existing collection or upsert to replace
      )
      os.remove(tmp_collection_file)

    
    # All objects with prefix
    objs = [i for i in BUCKET.objects.filter(Prefix=prefix) if '.tif' in i.key and "aux" not in i.key]

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        results = list(
            tqdm(
                executor.map(
                    lambda x: create_stac_item(x, collection["id"]), 
                    objs
                ), 
                total=len(objs) # sets total length of progressbar
            )
        ) 
    
    # Verify no failures: 
    failed = [x for x in results if isinstance(x, str) and x.startswith("FAILED:")]
    if len(failed): 
        print(f"FAILED: {len(failed)} (of {len(results)}). Aborting...")
        exit()
    
    else:
      print(f"{len(results)} Items created, write to file {tmp_items_file}")

    # # sort by date (to optimize loading) and dump to file for safekeeping
    with open(tmp_items_file, "w") as f: 
      f.write("\n".join([json.dumps(x.to_dict()) for x in sorted(results, key=lambda x: x.to_dict()["properties"]["datetime"])]))

    
    if not dry_run:
      # Load items into pgstac and then delete temp file
      pypgstac.load(
        table="items",
        file=tmp_items_file,
        dsn=dsn,
        method="insert_ignore", # use insert_ignore to avoid overwritting existing items or upsert to replace
      )
      os.remove(tmp_items_file)
    
    if not dry_run:
      con_str = make_conninfo(
          dbname=con_secrets["dbname"],
          user=con_secrets["username"],
          password=con_secrets["password"],
          host=con_secrets["host"],
          port=con_secrets["port"],
      )
      with psycopg.connect(con_str, autocommit=True) as conn:
        with conn.cursor() as cur:
            print("Adding default collection summaries")
            update_collection_summaries(cursor=cur,  collection_id=collection["id"])

    print("\nfin.")