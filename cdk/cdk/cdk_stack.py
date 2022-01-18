from aws_cdk import core
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
        # Discover function
        discover_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-discover-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="cmr-query",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"]
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=1024,
            timeout=core.Duration.seconds(30)
        )

        generate_cog_lambda = aws_lambda.Function(
            self,
            f"{id}-{collection}-generate-cog-fn",
            code=aws_lambda.Code.from_asset_image(
                directory="cogify",
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"]
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=4096,
            timeout=core.Duration.seconds(60),
            environment=dict(
                EARTHDATA_USERNAME=os.environ['EARTHDATA_USERNAME'],
                EARTHDATA_PASSWORD=os.environ['EARTHDATA_PASSWORD']
            )
        )
      

        ## State Machine Steps
        start_state = stepfunctions.Pass(self, "StartState")
        discover_task = tasks.LambdaInvoke(
            self, "Discover Granules Task",
            lambda_function=discover_lambda
        )
        generate_cog_task = tasks.LambdaInvoke(
            self, "Generate COG Task",
            lambda_function=generate_cog_lambda
        )
        map_cogs = stepfunctions.Map(self, "Map State",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload")
        )
        map_cogs.iterator(generate_cog_task)

        definition = start_state.next(discover_task).next(map_cogs)

        simple_state_machine = stepfunctions.StateMachine(self, f"{collection}-COG-StateMachine",
            definition=definition
        )

        # Rule to run it
        rule = events.Rule(self, "Schedule Rule",
            schedule=events.Schedule.cron(hour="1"),
            enabled=True
        )
        rule.add_target(
            targets.SfnStateMachine(simple_state_machine,
            input=events.RuleTargetInput.from_object({
                "collection": collection,
                "hours": 96,
                "version": version,
                "include": "^.+he5$"
            }))
        )
