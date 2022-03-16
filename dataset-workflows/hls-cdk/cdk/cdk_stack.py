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
from aws_cdk.aws_lambda_event_sources import SqsEventSource

SECRET_NAME = os.environ["SECRET_NAME"]

class CdkStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        stack_name = construct_id

        collection = "HLSS30.002"

        bucket = "climatedashboard-data"

        s3bucket = s3.Bucket.from_bucket_name(self, f"{id}-bucket", bucket_name=bucket)

        try:
            ndjson_bucket = s3.Bucket(
                self,
                "NDJsonBucket",
                bucket_name=f"{stack_name}-ndjson",
            )
        except:
            ndjson_bucket = s3.Bucket.from_bucket_name(
                self,
                "NDJsonBucket",
                bucket_name=f"{stack_name}-ndjson",
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

        ingest_queue = sqs.Queue(
            self,
            f"{id}-ingest-queue",
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,
                queue=sqs.Queue(self, id=f"{id}-cog-ingest-dead-letter-queue"),
            ),
            # same visibility as lambda function
            visibility_timeout=core.Duration.minutes(15),
        )
        ingest_queue.add_to_resource_policy(
            aws_iam.PolicyStatement(
                principals=[aws_iam.ServicePrincipal("s3.amazonaws.com")],
                actions=["SQS:SendMessage"],
                resources=[ingest_queue.queue_arn],
                conditions={"ArnEquals": {"aws:SourceArn": s3bucket.bucket_arn}},
            )
        )

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
        cmr_discover_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-discover-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/cmr-query",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=1024,
            timeout=core.Duration.minutes(15),
            environment={"QUEUE_URL": ingest_queue.queue_url},
        )
        cmr_discover_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["sqs:SendMessage"],
                resources=[ingest_queue.queue_arn],
            )
        )

        build_ndjson_role = aws_iam.Role(
            self,
            "BuildNDJsonRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        ingest_queue.grant_consume_messages(build_ndjson_role)
        ndjson_bucket.grant_write(build_ndjson_role)

        ndjson_dlq = sqs.Queue(
            self,
            "NDJsonDLQ",
            retention_period=core.Duration.days(14),
        )
        ndjson_queue = sqs.Queue(
            self,
            "NDJsonQueue",
            visibility_timeout=core.Duration.minutes(15),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=ndjson_dlq,
            ),
        )

        ndjson_queue.grant_send_messages(build_ndjson_role)
        build_ndjson_function = aws_lambda.Function(
            self,
            f"{id}-build_ndjson-lambda",
            role=build_ndjson_role,
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/ndjson-builder",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=8000,
            timeout=core.Duration.minutes(10),
            environment={
                "BUCKET": ndjson_bucket.bucket_name,
                "QUEUE_URL": ndjson_queue.queue_url,
                "COLLECTION": "HLSS30.002"
            },
        )

        item_event_source = SqsEventSource(
            ingest_queue,
            batch_size=100,
            max_batching_window=core.Duration.seconds(300),
            report_batch_item_failures=True,
        )
        build_ndjson_function.add_event_source(item_event_source)

        pgstac_loader_role = aws_iam.Role(
            self,
            "PGStacLoaderRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        ndjson_queue.grant_consume_messages(pgstac_loader_role)

        ndjson_bucket.grant_read(pgstac_loader_role)

        pgstac_secret = secretsmanager.Secret.from_secret_arn(
            self,
            id="PGStacSecret",
            secret_arn=SECRET_NAME,
        )

        pgstac_secret.grant_read(pgstac_loader_role)

        pgstac_security_group = ec2.SecurityGroup(
            self,
            f"{id}-pgstac-loader-sg",
            vpc=database_vpc,
            description="fromCogPipelinesPgstacLoader",
        )

        pgstac_loader = aws_lambda.Function(
            self,
            f"{id}-pgstac-loader-lambda",
            role=pgstac_loader_role,
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/pgstac-loader",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=8000,
            timeout=core.Duration.minutes(10),
            environment={
                "SECRET_NAME": SECRET_NAME,
            },
            reserved_concurrent_executions=3,
            vpc=database_vpc,
            #vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_groups=[lambda_function_security_group],
        )
        pgstac_loader.add_to_role_policy(ec2_network_access)

        ndjson_event_source = SqsEventSource(
            ndjson_queue,
            batch_size=5,
            max_batching_window=core.Duration.seconds(300),
            report_batch_item_failures=True,
        )
        pgstac_loader.add_event_source(ndjson_event_source)
