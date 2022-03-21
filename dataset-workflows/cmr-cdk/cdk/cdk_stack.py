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

        collection = "OMDOAO3e"
        version = "003"

        bucket = "climatedashboard-data"

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
        )


        generate_cog_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-generate-cog-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="../../lambdas/cogify",
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
                directory="../../lambdas/stac-gen",
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
                PGPASSWORD=os.environ["PGPASSWORD"],
            ),
            vpc=database_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_groups=[lambda_function_security_group],
        )

        db_write_lambda.add_to_role_policy(ec2_network_access)

        ## CMR Workflow State Machine Steps
        cmr_start_state = stepfunctions.Pass(self, "CMR Discovery StartState")
        cmr_discover_task = tasks.LambdaInvoke(
            self, "CMR Discover Granules Task", lambda_function=cmr_discover_lambda
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


        cmr_db_write_task = tasks.LambdaInvoke(
            self,
            "CMR DB Write task",
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

        cmr_wflow_definition = cmr_start_state.next(cmr_discover_task).next(map_cogs)

        cmr_wflow_state_machine = stepfunctions.StateMachine(
            self, f"{collection}-COG-StateMachine", definition=cmr_wflow_definition
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
