import os


# VPC that contains the target database to which STAC records will be inserted
VPC_ID = os.environ.get("VPC_ID")
SECURITY_GROUP_ID = os.environ.get("SECURITY_GROUP_ID")
ENV = os.environ.get("ENV")
SECRET_NAME = os.environ.get("SECRET_NAME")

APP_NAME = "delta-simple-ingest"
BUCKET_NAME = "climatedashboard-data"
