from aws_cdk import core
import aws_cdk.aws_stepfunctions as stepfunctions

class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        start_state = stepfunctions.Pass(self, "StartState")
        simple_state_machine = stepfunctions.StateMachine(self, "SkeletonStateMachine",
            definition=start_state
        )
        # The code that defines your stack goes here
