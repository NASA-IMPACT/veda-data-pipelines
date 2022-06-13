from sys import argv
import functools
import glob
import os

import boto3

DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "data")


sts = boto3.client("sts")
ACCOUNT_ID = sts.get_caller_identity().get("Account")
REGION = os.environ.get("AWS_REGION", "us-east-1")
APP_NAME = os.environ.get("APP_NAME")
ENV = os.environ.get("ENV", "dev")

DB_WRITE_FUNCTION_NAME = f"{APP_NAME}-{ENV}-lambda-db-write-fn"
INGESTION_STEP_MACHINE_ARN = f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{APP_NAME}-{ENV}-stepfunction-discover"


def arguments():
    if (len(argv) <= 1):
        print("No collection provided")
        return
    return argv[1:]

def data_files(data, data_path):
    files = []
    for item in data:
        files.extend(glob.glob(os.path.join(data_path,  f"{item}*.json")))
    return files

def args_handler(func):
    @functools.wraps(func)
    def prep_args(*args, **kwargs):
        internal_args = arguments()
        func(internal_args)
    return prep_args
