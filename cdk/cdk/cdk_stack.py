from aws_cdk import core
import aws_cdk.aws_stepfunctions as stepfunctions
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
from aws_cdk import aws_lambda

class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## State Machine and Rule to run it
        start_state = stepfunctions.Pass(self, "StartState")
        simple_state_machine = stepfunctions.StateMachine(self, "SkeletonStateMachine",
            definition=start_state
        )
        rule = events.Rule(self, "Schedule Rule",
            schedule=events.Schedule.cron(minute="1")
        )
        rule.add_target(targets.SfnStateMachine(simple_state_machine))

        # Discover function
        code_dir = "./"
        discover_function = aws_lambda.Function(
            self,
            f"modis-aod-discover-function",
            code=aws_lambda.Code.from_asset_image(
                directory=code_dir,
                file="cmr-query/Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric", "-c", "OMNO2d", "-d", 7, "--include ", "^.+he5$"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=1024,
            timeout=core.Duration.seconds(30)
        )
