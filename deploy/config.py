import os


ENV = os.environ.get("ENV")

COGNITO_APP_SECRET = os.environ["COGNITO_APP_SECRET"]
STAC_INGESTOR_URL = os.environ["STAC_INGESTOR_URL"]

EARTHDATA_USERNAME = os.environ.get("EARTHDATA_USERNAME", "XXXX")
EARTHDATA_PASSWORD = os.environ.get("EARTHDATA_PASSWORD", "XXXX")

APP_NAME = "veda-data-pipelines"
VEDA_DATA_BUCKET = "climatedashboard-data"
VEDA_EXTERNAL_BUCKETS = []
MCP_BUCKETS = {
    "prod": "nasa-maap-data-store",
    "stage": "nasa-maap-data-store",
    "dev": "nasa-maap-data-store"
}
STAC_API_ENDPOINT='https://az2kiic44c.execute-api.us-west-2.amazonaws.com/dev/stac'
STAC_PROVIDER='NASA_MAAP'

# This should throw if it is not provided
EXTERNAL_ROLE_ARN = os.environ["EXTERNAL_ROLE_ARN"]
