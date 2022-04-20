#!/usr/bin/env python3
import os
from aws_cdk import core

from cdk.cdk_stack import CdkStack


app = core.App()
CdkStack(
    app,
    f"simple-ingest-{os.environ.get('ENV')}",
    env=dict(
        region=os.environ["CDK_DEFAULT_REGION"],
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
    ),
)

app.synth()
