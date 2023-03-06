import os


ENV = os.environ.get("ENV")

COGNITO_APP_SECRET = os.environ["COGNITO_APP_SECRET"]
STAC_INGESTOR_URL = os.environ["STAC_INGESTOR_URL"]

EARTHDATA_USERNAME = os.environ.get("EARTHDATA_USERNAME", "XXXX")
EARTHDATA_PASSWORD = os.environ.get("EARTHDATA_PASSWORD", "XXXX")

APP_NAME = "veda-data-pipelines"
VEDA_DATA_BUCKET = "climatedashboard-data"
VEDA_EXTERNAL_BUCKETS = ["nasa-maap-data-store", "covid-eo-blackmarble"]
MCP_BUCKETS = {
    "prod": "veda-data-store",
    "stage": "veda-data-store-staging",
}

# This should throw if it is not provided
EXTERNAL_ROLE_ARN = os.environ["EXTERNAL_ROLE_ARN"]

VECTOR_SECRET_NAME = os.environ["VECTOR_SECRET_NAME"]
VECTOR_VPC_ID=os.environ["VECTOR_VPC_ID"]
VECTOR_SECURITY_GROUP=os.environ["VECTOR_SECURITY_GROUP"]
