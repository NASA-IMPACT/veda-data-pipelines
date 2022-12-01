import re
import boto3
import smart_open
import json
from uuid import uuid4
from airflow.models.variable import Variable

def assume_role(role_arn, session_name="veda-data-pipelines_s3-discovery"):

    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
    )
    return  {
            "aws_access_key_id": creds["AccessKeyId"],
            "aws_secret_access_key": creds.get("SecretAccessKey"),
            "aws_session_token": creds.get("SessionToken"),
        }
def get_s3_resp_iterator(bucket_name, prefix, s3_client, pagination_config={'page_size': 1000}):
    """
    Returns an s3 paginator.
    :param bucket_name: The bucket.
    :param prefix: The path for the s3 granules.
    :param s3_client: Initialized boto3 S3 client
    :param pagination_config: Configuration for s3 pagination
    """
    s3_paginator = s3_client.get_paginator('list_objects')
    return s3_paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
        PaginationConfig=pagination_config
    )

def discover_from_s3(response_iterator):
        """
        Fetch the link of the granules in the host url_path
        :return: Returns a dictionary containing the path, etag, and the last modified date of a granule
        
        """
        for page in response_iterator:
            for s3_object in page.get('Contents', {}):
                yield s3_object



def s3_discovery_handler(event, chunk_size = 2800):
    return {'collection': 'nex-gddp-cmip6-monthly-p10-hurs', 'prefix': 'monthly/CMIP6_ensemble_p10/hurs/', 'bucket': 'nex-gddp-cmip6-cog', 'filename_regex': '^.*.tif', 'discovery': 's3', 'datetime_range': 'month', 'cogify': False, 'payload': 's3://veda-uah-dev-impact-mwaa-853558080719/events/s3_discovery_handler_d3fe149c-f5e3-408b-a415-cc09fb376825.json'}
    bucket = event.get("bucket")
    prefix = event.get("prefix", "")
    filename_regex = event.get("filename_regex", None)
    collection = event.get("collection", prefix.rstrip("/"))
    properties = event.get("properties", {})
    event['cogify'] = event.pop("cogify", False)
    payload = {**event, "objects": []}
    # Propagate forward optional datetime arguments
    date_fields = {}
    if "single_datetime" in event:
        date_fields["single_datetime"] = event["single_datetime"]
    if "start_datetime" in event:
        date_fields["start_datetime"] = event["start_datetime"]
    if "end_datetime" in event:
        date_fields["end_datetime"] = event["end_datetime"]
    if "datetime_range" in event:
        date_fields["datetime_range"] = event["datetime_range"]
    
    role_arn = Variable.get('ASSUME_ROLE_ARN', default_var=False)
    kwargs = assume_role(role_arn=role_arn) if role_arn else {}
    s3client = boto3.client("s3", **kwargs)

    s3_iterator = get_s3_resp_iterator(bucket_name=bucket, prefix=prefix, s3_client=s3client)
    bucket_output = Variable.get('EVENT_BUCKET')
    key = f"s3://{bucket_output}/events/{collection}"
    records = 0
    out_keys = []
    discovered = 0
    for s3_object in discover_from_s3(s3_iterator):
        filename = s3_object["Key"]
        if filename_regex and not re.match(filename_regex, filename):
            continue
        file_obj = {
                "collection": collection,
                "s3_filename": f"s3://{bucket}/{filename}",
                "upload": event.get("upload", False),
                "properties": properties,
                **date_fields
            }

        payload["objects"].append(file_obj)
        if records == chunk_size:
            output_key = f"{key}/s3_discover_output_{uuid4()}.json"
            with smart_open.open(output_key, "w") as file:
                file.write(json.dumps(payload))
            out_keys.append(output_key)
            records = 0
            discovered += len(payload["objects"])
            payload["objects"] = []
        records += 1
    
    if payload["objects"]:
        output_key = f"{key}/s3_discover_output_{uuid4()}.json"
        discovered += len(payload["objects"])
        with smart_open.open(output_key, "w") as file:
            file.write(json.dumps(payload))
        out_keys.append(output_key)

    
    return {**event, 'payload': out_keys, 'discovered': discovered}