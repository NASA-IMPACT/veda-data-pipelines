#!/usr/bin/env python3
import os
from aws_cdk import core

from cdk.cdk_stack import CdkStack, DbCredentials

import config

app = core.App()
CdkStack(
    app,
    "cog-pipeline-no2-so2",
    env=dict(
        region=os.environ["CDK_DEFAULT_REGION"],
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
    ),
    vpc_id=config.VPC_ID,
    src_bucket_name=config.SRC_BUCKET_NAME,
    stac_bucket_name=config.STAC_BUCKET_NAME,
    collection=config.COLLECTION_NAME,
    db_credentials=DbCredentials(
        STAC_DB_HOST=config.STAC_DB_HOST,
        STAC_DB_USER=config.STAC_DB_USER,
        PGPASSWORD=config.PGPASSWORD,
    ),
)

app.synth()
