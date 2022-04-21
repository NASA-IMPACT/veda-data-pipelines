import os


# VPC that contains the target database to which STAC records will be inserted
VPC_ID = os.environ.get("VPC_ID")
SECURITY_GROUP_ID = os.environ.get("SECURITY_GROUP_ID")
ENV = os.environ.get("ENV")
APP_NAME = "SimpleIngest"
BUCKET_NAME = "climatedashboard-data"
