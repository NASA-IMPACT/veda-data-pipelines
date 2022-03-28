import os
import config
from aws_cdk import core, aws_iam, custom_resources
import aws_cdk.aws_stepfunctions as stepfunctions
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_lambda
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_s3 as s3

class CdkStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        stack_name = construct_id

        bucket = "climatedashboard-data"
        collection = "blue-tarp-detection"

        s3bucket = s3.Bucket.from_bucket_name(
            self, f"{id}-bucket", bucket_name=bucket
        )

        ec2_network_access = aws_iam.PolicyStatement(
            actions=[
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
            ],
            resources=["*"],
        )
        full_bucket_access = aws_iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject"],
            resources=[f"arn:aws:s3:::{bucket}/*"],
        )

        database_vpc = ec2.Vpc.from_lookup(self, f"{id}-vpc", vpc_id=config.VPC_ID)

        lambda_function_security_group = ec2.SecurityGroup(
            self,
            f"{id}-lambda-sg",
            vpc=database_vpc,
            description="fromCloudOptimizedPipelineLambdas",
        )

        lambda_function_security_group.add_egress_rule(
            ec2.Peer.any_ipv4(),
            connection=ec2.Port(protocol=ec2.Protocol("ALL"), string_representation=""),
            description="Allow lambda security group all outbound access",
        )
        # Discover function
        s3_discovery_lambda = aws_lambda.Function(
            self,
            f"{id}-{bucket}-discover-fn",
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

        s3_discovery_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"arn:aws:s3:::{bucket}/*"],
            )
        )
        s3_discovery_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[f"arn:aws:s3:::{bucket}"],
            )
        )

        generate_stac_item_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-generate-stac-item-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/stac-gen",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=4096,
            timeout=core.Duration.seconds(60)
        )
        generate_stac_item_lambda.add_to_role_policy(full_bucket_access)

        db_write_role = aws_iam.Role(
            self,
            "PGStacLoaderRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )


        db_write_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-write-db-fn",
            role=db_write_role,
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
            environment=dict(
                STAC_DB_HOST=os.environ["STAC_DB_HOST"],
                STAC_DB_USER=os.environ["STAC_DB_USER"],
                # TODO: Aimee - may want to be consistent about environment name for PG PASSWORD.
                # PGPASSWORD is the name of the variable used by the psql cli to load without requesting a password via a command line prompt.
                PGPASSWORD=os.environ["PGPASSWORD"],
            ),
            vpc=database_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_groups=[lambda_function_security_group],
        )

        db_write_lambda.add_to_role_policy(ec2_network_access)

        s3_start_state = stepfunctions.Pass(self, "S3 Discovery StartState")
        s3_discover_task = tasks.LambdaInvoke(
            self, "S3 Discover Task", lambda_function=s3_discovery_lambda
        )

        s3_generate_stac_item_task = tasks.LambdaInvoke(
            self,
            "S3 Generate STAC Item Task",
            lambda_function=generate_stac_item_lambda,
        )

        s3_db_write_task = tasks.LambdaInvoke(
            self,
            "S3 DB Write task",
            lambda_function=db_write_lambda,
            input_path="$.Payload",
        )

        map_stac_items = stepfunctions.Map(
            self,
            "Map STAC Item Generator",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        )

        # Create stac item for each element
        map_stac_items.iterator(s3_generate_stac_item_task.next(s3_db_write_task))

        s3_wflow_definition = s3_start_state.next(s3_discover_task).next(map_stac_items)

        s3_wflow_state_machine = stepfunctions.StateMachine(
            self, f"{bucket}-{collection}-COG-StateMachine", definition=s3_wflow_definition
        )
