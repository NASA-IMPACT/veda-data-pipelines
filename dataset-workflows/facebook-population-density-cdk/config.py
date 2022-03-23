import os


# VPC that contains the target database to which STAC records will be inserted
VPC_ID = os.environ.get("VPC_ID")

STAC_DB_HOST = os.environ.get("STAC_DB_HOST")
STAC_DB_USER = os.environ.get("STAC_DB_USER")
PGPASSWORD = os.environ.get("PGPASSWORD")
