from typing import TYPE_CHECKING
from aws_cdk import (
    core,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_event_sources,
)

if TYPE_CHECKING:
    from .lambda_stack import LambdaStack


class QueueStack(core.Stack):
    def __init__(
        self,
        app,
        construct_id: str,
        lambda_stack: "LambdaStack",
        **kwargs,
    ) -> None:
        super().__init__(app, construct_id, **kwargs)

        self.cogify_queue = self._queue(
            f"{construct_id}-cogify-queue",
            visibility_timeout=900,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,
                queue=self._queue(f"{construct_id}-cogify-dlq"),
            ),
        )

        lambda_stack.trigger_cogify_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.cogify_queue,
                batch_size=10,
                max_batching_window=core.Duration.seconds(20),
                report_batch_item_failures=True,
            )
        )

        self.stac_ready_queue = self._queue(
            f"{construct_id}-stac-ready-queue",
            visibility_timeout=900,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self._queue(f"{construct_id}-stac-ready-dlq", retention_days=14),
            ),
        )
        self.stac_ready_queue.grant_send_messages(lambda_stack.cogify_lambda.role)

        lambda_stack.trigger_ingest_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.stac_ready_queue,
                batch_size=10,
                max_batching_window=core.Duration.seconds(30),
                report_batch_item_failures=True,
            )
        )

        self.vector_queue = self._queue(
            f"{construct_id}-vector-queue",
            visibility_timeout=900,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,
                queue=self._queue(f"{construct_id}-vector-dlq"),
            ),
        )

        lambda_stack.trigger_vector_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                self.vector_queue,
                batch_size=10,
                max_batching_window=core.Duration.seconds(20),
                report_batch_item_failures=True,
            )
        )

    def _queue(
        self, name, visibility_timeout=30, dead_letter_queue=None, retention_days=4
    ):
        return sqs.Queue(
            self,
            name,
            queue_name=name,
            visibility_timeout=core.Duration.seconds(visibility_timeout),
            dead_letter_queue=dead_letter_queue,
            retention_period=core.Duration.days(retention_days),
        )
