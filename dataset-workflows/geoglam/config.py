import os


# VPC that contains the target database to which STAC records will be inserted
VPC_ID = os.environ["VPC_ID"]
STAC_DB_HOST = os.environ["STAC_DB_HOST"]
STAC_DB_USER = os.environ["STAC_DB_USER"]
PGPASSWORD = os.environ["PGPASSWORD"]

SRC_BUCKET_NAME = "covid-eo-data"
STAC_BUCKET_NAME = "climatedashboard-data"
COLLECTION_NAME = "agriculture-cropmonitor"
