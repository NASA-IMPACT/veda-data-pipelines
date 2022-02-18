from aws_cdk import core, aws_iam, custom_resources
import aws_cdk.aws_stepfunctions as stepfunctions
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
from aws_cdk import aws_lambda
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_s3
import os

VPC_ID = "vpc-0b0926e1be04a588d"


class CdkStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        collection = "OMDOAO3e"
        version = "003"

        bucket = "climatedashboard-data"
        prefix = "OMSO2PCA/"

        s3bucket = aws_s3.Bucket.from_bucket_name(
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

        database_vpc = ec2.Vpc.from_lookup(self, f"{id}-vpc", vpc_id=VPC_ID)

        ingest_queue = sqs.Queue(
            self,
            f"{id}-ingest-queue",
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,
                queue=sqs.Queue(self, id=f"{id}-cog-ingest-dead-letter-queue"),
            ),
            # same visibility as lambda function
            visibility_timeout=core.Duration.seconds(30),
        )
        ingest_queue.add_to_resource_policy(
            aws_iam.PolicyStatement(
                principals=[aws_iam.ServicePrincipal("s3.amazonaws.com")],
                actions=["SQS:SendMessage"],
                resources=[ingest_queue.queue_arn],
                conditions={"ArnEquals": {"aws:SourceArn": s3bucket.bucket_arn}},
            )
        )

        # In CDK, imported buckets implement IBucketProxy, as opposed to
        # Bucket, which makes it impossible to add an event notification
        # to an imported bucket using the `bucket.add_event_notification()`
        # function. Instead we have to implement the bucket notification
        # as a custome S3 SDK call
        custom_s3_sdk_call = custom_resources.AwsSdkCall(
            service="S3",
            action="putBucketNotificationConfiguration",
            parameters={
                "Bucket": s3bucket.bucket_name,
                "NotificationConfiguration": {
                    "QueueConfigurations": [
                        {
                            "Events": ["s3:ObjectCreated:*"],
                            "Filter": {
                                "Key": {
                                    "FilterRules": [
                                        {"Name": "prefix", "Value": "stac_item_queue"},
                                        {"Name": "suffix", "Value": ".json"},
                                    ]
                                }
                            },
                            "QueueArn": ingest_queue.queue_arn,
                        }
                    ]
                },
            },
            physical_resource_id=custom_resources.PhysicalResourceId.of(
                f"s3-notification-resource-cog-pipelines-1"
            ),
        )

        custom_notification = custom_resources.AwsCustomResource(
            self,
            "s3-sqs-notification",
            policy=custom_resources.AwsCustomResourcePolicy.from_statements(
                [
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        resources=[s3bucket.bucket_arn],
                        actions=["s3:PutBucketNotification"],
                    )
                ]
            ),
            on_create=custom_s3_sdk_call,
            on_update=custom_s3_sdk_call,
            # TODO: does `on_delete` needs to be implemented as well?
            # See: https://stackoverflow.com/a/61641858/15462881
        )

        custom_notification.node.add_dependency(s3bucket)
        custom_notification.node.add_dependency(ingest_queue)

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
                directory="s3-discovery",
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

        # Discover function
        cmr_discover_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-discover-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="cmr-query",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=1024,
            timeout=core.Duration.seconds(30),
        )

        generate_cog_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-generate-cog-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="cogify",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=4096,
            timeout=core.Duration.seconds(60),
            environment=dict(
                EARTHDATA_USERNAME=os.environ["EARTHDATA_USERNAME"],
                EARTHDATA_PASSWORD=os.environ["EARTHDATA_PASSWORD"],
            ),
        )

        generate_cog_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"arn:aws:s3:::{bucket}/*"],
            )
        )

        generate_stac_item_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-generate-stac-item-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="stac-gen",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=4096,
            timeout=core.Duration.seconds(60),
            environment=dict(
                EARTHDATA_USERNAME=os.environ["EARTHDATA_USERNAME"],
                EARTHDATA_PASSWORD=os.environ["EARTHDATA_PASSWORD"],
            ),
        )
        generate_stac_item_lambda.add_to_role_policy(full_bucket_access)

        db_write_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-write-db-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="db-write",
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
                STAC_DB_PASSWORD=os.environ["STAC_DB_PASSWORD"],
            ),
            vpc=database_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_groups=[lambda_function_security_group],
        )

        db_write_lambda.add_to_role_policy(ec2_network_access)

        ## CMR Workflow State Machine Steps
        cmr_start_state = stepfunctions.Pass(self, "CMR Discovery StartState")
        s3_start_state = stepfunctions.Pass(self, "S3 Discovery StartState")
        cmr_discover_task = tasks.LambdaInvoke(
            self, "CMR Discover Granules Task", lambda_function=cmr_discover_lambda
        )
        s3_discover_task = tasks.LambdaInvoke(
            self, "S3 Discover Task", lambda_function=s3_discovery_lambda
        )

        generate_cog_task = tasks.LambdaInvoke(
            self, "Generate COG Task", lambda_function=generate_cog_lambda
        )
        cmr_generate_stac_item_task = tasks.LambdaInvoke(
            self,
            "CMR Generate STAC Item Task",
            lambda_function=generate_stac_item_lambda,
            input_path="$.Payload",
        )

        s3_generate_stac_item_task = tasks.LambdaInvoke(
            self,
            "S3 Generate STAC Item Task",
            lambda_function=generate_stac_item_lambda,
        )

        cmr_db_write_task = tasks.LambdaInvoke(
            self,
            "CMR DB Write task",
            lambda_function=db_write_lambda,
            input_path="$.Payload",
        )

        s3_db_write_task = tasks.LambdaInvoke(
            self,
            "S3 DB Write task",
            lambda_function=db_write_lambda,
            input_path="$.Payload",
        )

        map_cogs = stepfunctions.Map(
            self,
            "Map COG and STAC Item Generator",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        )

        # Generate a cog and create stac item for each element
        map_cogs.iterator(
            generate_cog_task.next(cmr_generate_stac_item_task).next(cmr_db_write_task)
        )

        map_stac_items = stepfunctions.Map(
            self,
            "Map STAC Item Generator",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        )

        # Generate a cog and create stac item for each element
        map_stac_items.iterator(s3_generate_stac_item_task.next(s3_db_write_task))

        cmr_wflow_definition = cmr_start_state.next(cmr_discover_task).next(map_cogs)

        cmr_wflow_state_machine = stepfunctions.StateMachine(
            self, f"{collection}-COG-StateMachine", definition=cmr_wflow_definition
        )

        s3_wflow_definition = s3_start_state.next(s3_discover_task).next(map_stac_items)

        s3_wflow_state_machine = stepfunctions.StateMachine(
            self, f"{bucket}-{prefix}-COG-StateMachine", definition=s3_wflow_definition
        )

        # Rule to run it
        rule = events.Rule(
            self, "Schedule Rule", schedule=events.Schedule.cron(hour="1"), enabled=True
        )
        rule.add_target(
            targets.SfnStateMachine(
                cmr_wflow_state_machine,
                input=events.RuleTargetInput.from_object(
                    {
                        "collection": collection,
                        "hours": 96,
                        "version": version,
                        "include": "^.+he5$",
                    }
                ),
            )
        )
