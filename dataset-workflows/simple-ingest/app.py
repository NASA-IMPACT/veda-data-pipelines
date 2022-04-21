#!/usr/bin/env python3
import os
from aws_cdk import (
    core,
)

from cdk.lambda_stack import LambdaStack
from cdk.iam_policies import IamPolicies
from cdk.step_function_stack import StepFunctionStack
from cdk.vpc_stack import VpcStack

import config


app = core.App()

env_details = core.Environment(
    region=os.environ["CDK_DEFAULT_REGION"],
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
)

iam_stack = IamPolicies(
    config.BUCKET_NAME
)

vpc_stack = VpcStack(
    app,
    f"{config.APP_NAME}-vpc",
    vpc=config.VPC_ID,
    sg=config.SECURITY_GROUP_ID,
    env=env_details,
)
lambda_stack = LambdaStack(
    app,
    f"{config.APP_NAME}-lambda",
    database_vpc=vpc_stack._database_vpc,
    iam_stack=iam_stack,
    env=env_details
)

vpc_stack.add_rds_write_ingress(lambda_stack.lambda_sg)

step_function_stack = StepFunctionStack(
    app,
    f"{config.APP_NAME}-stepfunction",
    **lambda_stack.lambdas,
    env=env_details
)

app.synth()
