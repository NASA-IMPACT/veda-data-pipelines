#!/usr/bin/env python3
import os
from aws_cdk import (
    core,
)

from cdk.lambda_stack import LambdaStack
from cdk.step_function_stack import StepFunctionStack
from cdk.vpc_stack import VpcStack
from cdk.queue_stack import QueueStack
from cdk.iam_policies import IamPolicies

import config

def integrate_to_lambdas(trigger_cogify_lambda, trigger_ingest_lambda, cogify_arn, pub_arn):
    # this lambda is triggered by SQS queue and in turn triggers execution of the publication step function
    trigger_cogify_lambda.add_to_role_policy(IamPolicies.stepfunction_start_execution_access(cogify_arn))
    trigger_ingest_lambda.add_to_role_policy(IamPolicies.stepfunction_start_execution_access(pub_arn))

    trigger_cogify_lambda.add_environment("STEP_FUNCTION_ARN", cogify_arn)
    trigger_ingest_lambda.add_environment("STEP_FUNCTION_ARN", pub_arn)

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
    env=env_details
)

vpc_stack.add_rds_write_ingress(lambda_stack.lambda_sg)

step_function_stack = StepFunctionStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-stepfunction",
    lambda_stack,
    env=env_details
)

arns = step_function_stack.get_arns(env_details)

integrate_to_lambdas(
    lambda_stack.lambdas["trigger_cogify_lambda"],
    lambda_stack.lambdas["trigger_ingest_lambda"],
    arns[0],
    arns[1],
)

queue_stack = QueueStack(
    app,
    f"{config.APP_NAME}-{config.ENV}-queue",
    lambda_stack,
    env=env_details
)


app.synth()
