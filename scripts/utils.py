from sys import argv
import functools
import glob
import os
import base64
import json
import requests
import boto3

DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "data")


sts = boto3.client("sts")
ACCOUNT_ID = sts.get_caller_identity().get("Account")
REGION = os.environ.get("AWS_REGION", "us-west-2")
APP_NAME = os.environ.get("APP_NAME")
ENV = os.environ.get("ENV", "dev")

SUBMIT_STAC_FUNCTION_NAME = f"{APP_NAME}-{ENV}-lambda-submit-stac-fn"
INGESTION_STEP_MACHINE_ARN = f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{APP_NAME}-{ENV}-stepfunction-discover"
DISCOVERY_TRIGGER_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{APP_NAME}-{ENV}-lambda-trigger-discover-fn"

def arguments():
    if len(argv) <= 1:
        print("No collection provided")
        return
    return argv[1:]

def cmr_records(collection):
    provider = 'NASA_MAAP'
    CMR_STAC_ENDPOINT = 'https://az2kiic44c.execute-api.us-west-2.amazonaws.com/dev/stac'
    url = f"{CMR_STAC_ENDPOINT}/{provider}/collections/{collection}"
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        filename = f"../data/collections/{collection}.json"
        with open(filename, "w+") as f:
            data = json.loads(response.text)
            json.dump(data, f, indent=2)
            f.close()
        print (f"Wrote to file {filename}")
        return filename
    else:
        print(f"Got {response.status_code} resonse for {url}")

def data_files(data, data_path):
    files = []
    for item in data:
        files.extend(glob.glob(os.path.join(data_path, f"{item}*.json")))
    # If there are no files already in existence, check CMR for the data
    if len(files) == 0:
        for item in data:
            filename = cmr_records(item)
            files.append(filename)
    return files


def args_handler(func):
    @functools.wraps(func)
    def prep_args(*args, **kwargs):
        internal_args = arguments()
        func(internal_args)

    return prep_args


def get_secret(secret_name: str) -> None:
    """Retrieve secrets from AWS Secrets Manager

    Args:
        secret_name (str): name of aws secrets manager secret containing database connection secrets
        profile_name (str, optional): optional name of aws profile for use in debugger only

    Returns:
        secrets (dict): decrypted secrets in dict
    """

    # Create a Secrets Manager client
    session = boto3.session.Session(region_name="us-west-2")
    client = session.client(service_name="secretsmanager")

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    # Decrypts secret using the associated KMS key.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    if "SecretString" in get_secret_value_response:
        return json.loads(get_secret_value_response["SecretString"])
    else:
        return json.loads(base64.b64decode(get_secret_value_response["SecretBinary"]))
