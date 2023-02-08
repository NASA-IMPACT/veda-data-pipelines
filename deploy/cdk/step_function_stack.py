from typing import TYPE_CHECKING
from aws_cdk import (
    core,
    aws_stepfunctions as stepfunctions,
    aws_stepfunctions_tasks as tasks,
)


if TYPE_CHECKING:
    from .queue_stack import QueueStack
    from .lambda_stack import LambdaStack


class StepFunctionStack(core.Stack):
    def __init__(
        self,
        app,
        construct_id: str,
        lambda_stack: "LambdaStack",
        queue_stack: "QueueStack",
        **kwargs,
    ):
        super().__init__(app, construct_id, **kwargs)
        self.construct_id = construct_id

        self.cogify_workflow = self._cogify_workflow(
            lambda_stack=lambda_stack,
            queue_stack=queue_stack,
        )
        self.discovery_workflow = self._discovery_workflow(
            lambda_stack=lambda_stack,
            queue_stack=queue_stack,
        )
        self.vector_workflow = self._vector_workflow(
            lambda_stack=lambda_stack,
            queue_stack=queue_stack,
        )

        self.publication_workflow = self._publication_workflow(
            lambda_stack=lambda_stack,
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
        lambda_stack: "LambdaStack",
        queue_stack: "QueueStack",
    ) -> stepfunctions.StateMachine:
        s3_discovery_task = self._lambda_task(
            "S3 Discover Task",
            lambda_stack.s3_discovery_lambda,
        )

        cmr_discovery_task = self._lambda_task(
            "CMR Discover Task",
            lambda_stack.cmr_discovery_lambda,
        )

        enqueue_cogify_task = self._sqs_task(
            "Send to Cogify queue",
            queue=queue_stack.cogify_queue,
        )

        enqueue_ready_task = self._sqs_task(
            "Send to stac-ready queue",
            queue=queue_stack.stac_ready_queue,
        )

        enqueue_vector_task = self._sqs_task(
            "Send to vector queue",
            queue=queue_stack.vector_queue,
        )

        vector_or_cogify = (
            stepfunctions.Choice(self, "Vector or Cogify?")
            .when(
                stepfunctions.Condition.boolean_equals("$.Payload.vector", True),
                stepfunctions.Map(
                    self,
                    "Run queueing to vector queue",
                    max_concurrency=100,
                    items_path=stepfunctions.JsonPath.string_at("$.Payload.objects"),
                ).iterator(enqueue_vector_task),
            )
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
                s3_discovery_task.next(vector_or_cogify),
            )
            .when(
                stepfunctions.Condition.string_equals("$.discovery", "cmr"),
                cmr_discovery_task.next(vector_or_cogify),
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
        lambda_stack: "LambdaStack",
        queue_stack: "QueueStack",
    ) -> stepfunctions.StateMachine:
        cogify_task = self._lambda_task(
            "Cogify",
            lambda_stack.cogify_lambda,
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

    def _vector_workflow(
        self,
        lambda_stack: "LambdaStack",
        queue_stack: "QueueStack",
    ) -> stepfunctions.StateMachine:
        vector_task = self._lambda_task(
            "Ingest Vector",
            lambda_stack.vector_lambda,
        )

        # enqueue_task = self._sqs_task(
        #     "Send cogified to stac-ready queue",
        #     queue=queue_stack.stac_ready_queue,
        #     input_path="$.Payload",
        # )

        vector_workflow = stepfunctions.Map(
            self,
            "Run vector ingest",
            max_concurrency=100,
            items_path=stepfunctions.JsonPath.string_at("$"),
        ).iterator(vector_task)

        return stepfunctions.StateMachine(
            self,
            f"vector-sf",
            state_machine_name=f"{self.stack_name}-cogify",
            definition=vector_workflow,
        )

    def _publication_workflow(
        self,
        lambda_stack: "LambdaStack",
    ) -> stepfunctions.StateMachine:

        transfer_task = self._lambda_task(
            "Data Transfer Task",
            lambda_stack.data_transfer_lambda,
            output_path="$.Payload",
        )

        build_stac_item_task = self._lambda_task(
            "Build STAC Task",
            lambda_stack.build_stac_lambda,
            output_path="$.Payload",
        )

        build_stac_item_task.add_retry(
            errors=["RasterioIOError"],
            interval=core.Duration.seconds(2),
            max_attempts=5,
        )

        submit_stac_item_task = self._lambda_task(
            "Submit to STAC Ingestor Task",
            lambda_stack.submit_stac_lambda,
            input_path="$",
        )

        build_and_submit_stac_items = stepfunctions.Map(
            self,
            "Submit to STAC Ingestor",
            max_concurrency=100,
            items_path=stepfunctions.JsonPath.string_at("$"),
        ).iterator(build_stac_item_task.next(submit_stac_item_task))

        publish_workflow = transfer_task.next(build_and_submit_stac_items)

        return stepfunctions.StateMachine(
            self,
            "publication-sf",
            state_machine_name=f"{self.stack_name}-publication",
            definition=publish_workflow,
        )

    def build_arn(self, env_vars, key):
        base_str = f"arn:aws:states:{env_vars.region}:{env_vars.account}:stateMachine:"
        return f"{base_str}{self.construct_id}-{key}"
