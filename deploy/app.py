#!/usr/bin/env python3
import os
from aws_cdk import core

from cdk.lambda_stack import LambdaStack
from cdk.step_function_stack import StepFunctionStack
from cdk.vpc_stack import VpcStack
from cdk.queue_stack import QueueStack

import config


app = core.App()

env_details = core.Environment(
    region=os.environ["CDK_DEFAULT_REGION"],
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
)

vpc_stack = VpcStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-vpc",
    vpc=config.VPC_ID,
    sg=config.SECURITY_GROUP_ID,
    env=env_details,
)
lambda_stack = LambdaStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-lambda",
    database_vpc=vpc_stack._database_vpc,
    env=env_details,
)

vpc_stack.add_rds_write_ingress(lambda_stack.lambda_sg)

queue_stack = QueueStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-queue",
    lambda_stack,
    env=env_details,
)

step_function_stack = StepFunctionStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-stepfunction",
    lambda_stack,
    queue_stack,
    env=env_details,
)

lambda_stack.grant_execution_privileges(
    lambda_function=lambda_stack.lambdas["trigger_cogify_lambda"],
    workflow=step_function_stack.cogify_workflow,
)
lambda_stack.grant_execution_privileges(
    lambda_function=lambda_stack.lambdas["trigger_ingest_lambda"],
    workflow=step_function_stack.publication_workflow,
)

app.synth()
