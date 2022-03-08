#!/usr/bin/env python3
import os
from aws_cdk import core

from cdk.cdk_stack import CdkStack


app = core.App()
CdkStack(
    app,
    "cog-pipeline-cmr-query",
    env=dict(
        region=os.environ["CDK_DEFAULT_REGION"],
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
    ),
)

app.synth()
