from typing import Dict, TypedDict
from aws_cdk import core
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_lambda
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_iam as iam


class CdkStack(core.Stack):
    def __init__(
        self,
        scope: core.Construct,
        *,
        vpc_id: str,
        src_bucket_name: str,
        stac_bucket_name: str,
        collection: str,
        db_credentials: "DbCredentials",
        **kwargs,
    ) -> None:
        super().__init__(scope, **kwargs)

        s3_discovery_lambda = self.build_s3_discover_lambda()
        self.get_bucket(src_bucket_name).grant_read(s3_discovery_lambda)

        generate_stac_item_lambda = self.build_stac_generation_lambda()
        self.get_bucket(stac_bucket_name).grant_read_write(generate_stac_item_lambda)

        db_vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id=vpc_id)
        db_write_lambda = self.build_db_write_lambda(
            vpc=db_vpc, db_credentials=db_credentials
        )

        workflow = tasks.LambdaInvoke(
            self,
            "S3 Discover Task",
            lambda_function=s3_discovery_lambda,
        ).next(
            stepfunctions.Map(
                self,
                "Map STAC Item Generator",
                max_concurrency=10,
                items_path=stepfunctions.JsonPath.string_at("$.Payload"),
            ).iterator(
                tasks.LambdaInvoke(
                    self,
                    "S3 Generate STAC Item Task",
                    lambda_function=generate_stac_item_lambda,
                ).next(
                    tasks.LambdaInvoke(
                        self,
                        "S3 DB Write task",
                        lambda_function=db_write_lambda,
                        input_path="$.Payload",
                    )
                )
            )
        )

        # Create stac item for each element
        stepfunctions.StateMachine(
            self,
            f"{src_bucket_name}-{collection}-COG-StateMachine",
            definition=workflow,
        )

    def get_bucket(self, bucket_name: str) -> s3.IBucket:
        return s3.Bucket.from_bucket_name(self, bucket_name, bucket_name=bucket_name)

    def build_s3_discover_lambda(self) -> aws_lambda.IFunction:
        return aws_lambda.Function(
            self,
            "discover-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/s3-discovery",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=1024,
            timeout=core.Duration.seconds(30),
        )

    def build_stac_generation_lambda(self) -> aws_lambda.IFunction:
        return aws_lambda.Function(
            self,
            "generate-stac-item-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/stac-gen",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=4096,
            timeout=core.Duration.seconds(60),
        )

    def build_db_write_lambda(
        self, vpc: ec2.IVpc, db_credentials: "DbCredentials"
    ) -> aws_lambda.IFunction:
        security_group = ec2.SecurityGroup(
            self,
            f"lambda-sg",
            vpc=vpc,
            description="fromCloudOptimizedPipelineLambdas",
        )
        security_group.add_egress_rule(
            ec2.Peer.any_ipv4(),
            connection=ec2.Port(protocol=ec2.Protocol("ALL"), string_representation=""),
            description="Allow lambda security group all outbound access",
        )

        func = aws_lambda.Function(
            self,
            "write-db-fn",
            role=iam.Role(
                self,
                "PGStacLoaderRole",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"
                    )
                ],
            ),
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/db-write",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=4096,
            timeout=core.Duration.seconds(60),
            environment=db_credentials,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_groups=[security_group],
        )

        func.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                ],
                resources=["*"],
            )
        )
        return func


class DbCredentials(TypedDict):
    STAC_DB_HOST: str
    STAC_DB_USER: str
    PGPASSWORD: str
