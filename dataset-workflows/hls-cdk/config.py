import os


# VPC that contains the target database to which STAC records will be inserted
VPC_ID = os.environ.get("VPC_ID")
ENV = os.environ.get("ENV")
SECRET_NAME = os.environ["SECRET_NAME"]
