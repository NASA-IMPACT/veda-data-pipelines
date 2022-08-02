from typing import Dict, TYPE_CHECKING
from aws_cdk import (
    core,
    aws_stepfunctions as stepfunctions,
    aws_stepfunctions_tasks as tasks,
    aws_lambda,
)

import config


if TYPE_CHECKING:
    from .queue_stack import QueueStack


class StepFunctionStack(core.Stack):
    def __init__(self, app, construct_id, lambda_stack, queue_stack, **kwargs):
        super().__init__(app, construct_id, **kwargs)

        self.cogify_workflow = self._cogify_workflow(
            lambdas=lambda_stack.lambdas,
            queue_stack=queue_stack,
        )
        self.discovery_workflow = self._discovery_workflow(
            lambdas=lambda_stack.lambdas,
            queue_stack=queue_stack,
        )
        self.publication_workflow = self._publication_workflow(
            lambdas=lambda_stack.lambdas,
        )

    def _lambda_task(self, name, lambda_function, input_path=None, output_path=None):
        return tasks.LambdaInvoke(
            self,
            name,
            lambda_function=lambda_function,
            input_path=input_path,
            output_path=output_path,
        )

    def _sqs_task(self, name, queue, input_path="$"):
        return tasks.SqsSendMessage(
            self,
            name,
            queue=queue,
            message_body=stepfunctions.TaskInput.from_json_path_at(input_path),
        )

    def _discovery_workflow(
        self,
        lambdas: Dict[str, aws_lambda.IFunction],
        queue_stack: "QueueStack",
    ) -> stepfunctions.StateMachine:
        s3_discovery_task = self._lambda_task(
            "S3 Discover Task",
            lambdas["s3_discovery_lambda"],
        )

        cmr_discovery_task = self._lambda_task(
            "CMR Discover Task",
            lambdas["cmr_discovery_lambda"],
        )

        enqueue_cogify_task = self._sqs_task(
            "Send to Cogify queue",
            queue=queue_stack.cogify_queue,
        )

        enqueue_ready_task = self._sqs_task(
            "Send to stac-ready queue",
            queue=queue_stack.stac_ready_queue,
        )

        maybe_cogify = (
            stepfunctions.Choice(self, "Cogify?")
            .when(
                stepfunctions.Condition.boolean_equals("$.Payload.cogify", True),
                stepfunctions.Map(
                    self,
                    "Run concurrent queueing to cogify queue",
                    max_concurrency=100,
                    items_path=stepfunctions.JsonPath.string_at("$.Payload.objects"),
                ).iterator(enqueue_cogify_task),
            )
            .otherwise(
                stepfunctions.Map(
                    self,
                    "Run concurrent queueing to stac ready queue",
                    max_concurrency=100,
                    items_path=stepfunctions.JsonPath.string_at("$.Payload.objects"),
                ).iterator(enqueue_ready_task)
            )
        )

        discovery_workflow = (
            stepfunctions.Choice(self, "Discovery Choice (CMR or S3)")
            .when(
                stepfunctions.Condition.string_equals("$.discovery", "s3"),
                s3_discovery_task.next(maybe_cogify),
            )
            .when(
                stepfunctions.Condition.string_equals("$.discovery", "cmr"),
                cmr_discovery_task.next(maybe_cogify),
            )
            .otherwise(stepfunctions.Fail(self, "Discovery Type not supported"))
        )

        return stepfunctions.StateMachine(
            self,
            "discover-sf",
            state_machine_name=f"{self.stack_name}-discover",
            definition=discovery_workflow,
        )

    def _cogify_workflow(
        self,
        lambdas: Dict[str, aws_lambda.IFunction],
        queue_stack: "QueueStack",
    ) -> stepfunctions.StateMachine:
        cogify_task = self._lambda_task(
            "Cogify",
            lambdas["cogify_lambda"],
        )

        enqueue_task = self._sqs_task(
            "Send cogified to stac-ready queue",
            queue=queue_stack.stac_ready_queue,
            input_path="$.Payload",
        )

        cogify_workflow = stepfunctions.Map(
            self,
            "Run concurrent cogifications",
            max_concurrency=100,
            items_path=stepfunctions.JsonPath.string_at("$"),
        ).iterator(cogify_task.next(enqueue_task))

        return stepfunctions.StateMachine(
            self,
            f"cogify-sf",
            state_machine_name=f"{self.stack_name}-cogify",
            definition=cogify_workflow,
        )

    def _publication_workflow(
        self,
        lambdas: Dict[str, aws_lambda.IFunction],
    ) -> stepfunctions.StateMachine:
        publish_task = self._lambda_task(
            "Build Ndjson Task",
            lambdas["build_ndjson_lambda"],
        )

        submit_task = self._lambda_task(
            "Submit to STAC Ingestor Task",
            lambdas["submit_stac_lambda"],
            input_path="$.Payload",
        )

        transfer_task = self._lambda_task(
            "Data Transfer",
            lambdas["data_transfer_lambda"],
            output_path="$.Payload",
        )

        publish_workflow = (
            transfer_task.next(publish_task)
            if config.ENV in ["stage", "prod"]
            else publish_task
        ).next(
            stepfunctions.Map(
                self,
                "Submit to STAC Ingestor",
                max_concurrency=100,
                items_path=stepfunctions.JsonPath.string_at("$"),
            ).iterator(submit_task)
        )

        return stepfunctions.StateMachine(
            self,
            "publication-sf",
            state_machine_name=f"{self.stack_name}-publication",
            definition=publish_workflow,
        )
