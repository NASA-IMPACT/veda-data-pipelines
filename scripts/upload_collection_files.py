import boto3
from os import listdir
from os.path import isfile, join
import argparse

# Upload collection files to S3, which the API will read from
# TODO: How to configure deployment of the API and cloud-optimized data generation / publishing files.

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument('-d', '--deployment', help='Deployment name')
args = parser.parse_args()
s3 = boto3.client('s3')
deployment = args.deployment
data_dir = f"datasets/{deployment}"

# TODO: Make this configurable
bucket = 'cumulus-map-internal'
s3_directory = 'cloud-optimized/collections'

collection_files = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]

for collection_filename in collection_files:
    print(f"Uploading {collection_filename}")
    response = s3.upload_file(
        f"{data_dir}/{collection_filename}",
        bucket,
        f"{s3_directory}/{collection_filename}",
        ExtraArgs={'ACL': 'public-read'}
    )
    print(response)

