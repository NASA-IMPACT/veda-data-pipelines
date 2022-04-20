import os


# VPC that contains the target database to which STAC records will be inserted
VPC_ID = os.environ.get("VPC_ID")
ENV = os.environ.get("ENV")
SECURITY_GROUP_ID = os.environ.get("SECURITY_GROUP_ID")
SECRET_NAME = os.environ.get("SECRET_NAME")
COLLECTION = os.environ.get("COLLECTION")
