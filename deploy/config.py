import os


# VPC that contains the target database to which STAC records will be inserted
ENV = os.environ.get("ENV")

COGNITO_APP_SECRET = os.environ["COGNITO_APP_SECRET"]
STAC_INGESTOR_URL = os.environ["STAC_INGESTOR_URL"]

EARTHDATA_USERNAME = os.environ.get("EARTHDATA_USERNAME")
EARTHDATA_PASSWORD = os.environ.get("EARTHDATA_PASSWORD")

APP_NAME = "delta-simple-ingest"
VEDA_DATA_BUCKET = "climatedashboard-data"
VEDA_EXTERNAL_BUCKETS = ["nasa-maap-data-store", "covid-eo-blackmarble"]
MCP_BUCKETS = {
    "prod": "veda-data-store",
    "stage": "veda-data-store-staging",
}

EXTERNAL_ROLE_ARN = os.environ.get("EXTERNAL_ROLE_ARN")
