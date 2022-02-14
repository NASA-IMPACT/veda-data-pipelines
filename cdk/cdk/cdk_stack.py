from aws_cdk import (core, aws_iam)
import aws_cdk.aws_stepfunctions as stepfunctions
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
from aws_cdk import aws_lambda
from aws_cdk import aws_stepfunctions_tasks as tasks
import os


class CdkStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        collection = "OMDOAO3e"
        version = "003"

        bucket = "climatedashboard-data"
        prefix= "OMSO2PCA/"
        # Discover function
        s3_discover_lambda = aws_lambda.Function(
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
                resources=[
                    f"arn:aws:s3:::{bucket}/*"
                ],
            )
        )
        s3_discovery_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[
                    f"arn:aws:s3:::{bucket}"
                ],
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
                EARTHDATA_PASSWORD=os.environ["EARTHDATA_PASSWORD"]
            ),
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
                STAC_DB_HOST = os.environ['STAC_DB_HOST'],
                STAC_DB_USER = os.environ['STAC_DB_USER'],
                STAC_DB_PASSWORD = os.environ['STAC_DB_PASSWORD']
            ),
        )

        ## CMR Workflow State Machine Steps
        cmr_start_state = stepfunctions.Pass(self, "CMR Discovery StartState")
        s3_start_state = stepfunctions.Pass(self, "S3 Discovery StartState")
        cmr_discover_task = tasks.LambdaInvoke(
            self, "CMR Discover Granules Task", lambda_function=cmr_discover_lambda
        )
        s3_discover_task = tasks.LambdaInvoke(
            self, "S3 Discover Task", lambda_function=s3_discover_lambda
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
            lambda_function=generate_stac_item_lambda
        )


        map_cogs = stepfunctions.Map(
            self,
            "Map COG and STAC Item Generator",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        )

        # Generate a cog and create stac item for each element
        map_cogs.iterator(generate_cog_task.next(cmr_generate_stac_item_task))


        map_stac_items = stepfunctions.Map(
            self,
            "Map STAC Item Generator",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        )

        # Generate a cog and create stac item for each element
        map_stac_items.iterator(s3_generate_stac_item_task)


        cmr_wflow_definition = cmr_start_state.next(cmr_discover_task).next(map_cogs)

        cmr_wflow_state_machine= stepfunctions.StateMachine(
            self, f"{collection}-COG-StateMachine", definition=cmr_wflow_definition
        )

        s3_wflow_definition= s3_start_state.next(s3_discover_task).next(map_stac_items)

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
