import os
from aws_cdk import (
    core,
    aws_iam,
    aws_stepfunctions as stepfunctions,
    aws_lambda,
    aws_stepfunctions_tasks as tasks,
    aws_ec2 as ec2,
)
import config

class LambdaStack:
    def __init__(self) -> None:
        

    def _lambda(self, name, dir, memory_size=1024, timeout=30, env=None, vpc=None, security_groups=None):
        return aws_lambda.Function(
            self,
            name,
            function_name=name,
            code=aws_lambda.Code.from_asset_image(
                directory=dir,
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=memory_size,
            timeout=core.Duration.seconds(timeout),
            environment=env,
            vpc=vpc,
            security_groups=security_groups,
        )
