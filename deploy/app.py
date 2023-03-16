#!/usr/bin/env python3
import os
import subprocess
from getpass import getuser

import aws_cdk
from aws_cdk import App, Environment

from cdk.lambda_stack import LambdaStack
from cdk.step_function_stack import StepFunctionStack
from cdk.queue_stack import QueueStack
from cdk.util_stack import DataPipelineUtilStack

import config as cfg

app = App()

config = cfg.Config(_env_file=".env")

git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
try:
    git_tag = subprocess.check_output(["git", "describe", "--tags"]).decode().strip()
except subprocess.CalledProcessError:
    git_tag = "no-tag"

tags = {
    "Project": "veda",
    "Owner": config.owner,
    "Client": "nasa-impact",
    "Stack": config.ENV,
    "GitCommit": git_sha,
    "GitTag": git_tag,
}

env_details = Environment(
    region=os.environ["CDK_DEFAULT_REGION"],
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
)

lambda_stack = LambdaStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-lambda",
    env=env_details,
)

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

# ENV secret, OIDC support (if enabled)
util_stack = DataPipelineUtilStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-util",
    config=config,
)


# Need to build arn manually otherwise it'll result in cyclic dependency
cogify_arn = step_function_stack.build_arn(env_details, "cogify")
pub_arn = step_function_stack.build_arn(env_details, "publication")
vector_arn = step_function_stack.build_arn(env_details, "vector-ingest")

lambda_stack.grant_execution_privileges(
    lambda_function=lambda_stack.trigger_cogify_lambda,
    workflow_arn=cogify_arn,
)
lambda_stack.grant_execution_privileges(
    lambda_function=lambda_stack.trigger_ingest_lambda,
    workflow_arn=pub_arn,
)
lambda_stack.grant_execution_privileges(
    lambda_function=lambda_stack.trigger_vector_lambda,
    workflow_arn=vector_arn,
)


for key, value in tags.items():
    aws_cdk.Tags.of(app).add(key, value)

app.synth()
