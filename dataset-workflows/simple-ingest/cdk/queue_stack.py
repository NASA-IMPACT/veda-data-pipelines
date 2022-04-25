from aws_cdk import (
    core,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_lambda_event_sources as lambda_event_sources,
)


class QueueStack(core.Stack):
    def __init__(self, app, construct_id, lambda_stack, **kwargs) -> None:
        super().__init__(app, construct_id, **kwargs)

        build_ndjson_lambda = lambda_stack.lambdas["build_ndjson_lambda"]
        pgstac_loader_lambda = lambda_stack.lambdas["pgstac_loader_lambda"]

        ndjson_bucket = self._bucket(f"cogpipeline-ndjson")
        ndjson_bucket.grant_read_write(build_ndjson_lambda.role)
        ndjson_bucket.grant_read(pgstac_loader_lambda.role)
        
        discovered_queue = self._queue(f"{construct_id}-discovered-queue",
            visibility_timeout=600,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,
                queue=self._queue(f"{construct_id}-discovered-dlq"),
            ),
        )
        discovered_queue.grant_send_messages(lambda_stack.lambdas["cmr_discovery_lambda"].role)

        build_ndjson_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                discovered_queue,
                batch_size=100,
                max_batching_window=core.Duration.seconds(300),
                report_batch_item_failures=True,
            )
        )

        ndjson_queue = self._queue(f"{construct_id}-ndjson-queue",
            visibility_timeout=600,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self._queue(f"{construct_id}-ndjson-dlq", retention_days=14),
            )
        )
        ndjson_queue.grant_send_messages(build_ndjson_lambda.role)

        build_ndjson_lambda.add_environment("BUCKET", ndjson_bucket.bucket_name)
        build_ndjson_lambda.add_environment("QUEUE_URL", ndjson_queue.queue_url)

        pgstac_loader_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                ndjson_queue,
                batch_size=100,
                max_batching_window=core.Duration.seconds(300),
                report_batch_item_failures=True,
            )
        )
        ndjson_queue.grant_consume_messages(lambda_stack.lambdas["pgstac_loader_lambda"].role)

    def _queue(self, name, visibility_timeout=30, dead_letter_queue=None, retention_days=4):
        return sqs.Queue(
            self,
            name,
            queue_name=name,
            visibility_timeout=core.Duration.seconds(visibility_timeout),
            dead_letter_queue=dead_letter_queue,
            retention_period=core.Duration.days(retention_days),
        )

    def _bucket(self, name):
        try:
            ndjson_bucket = s3.Bucket(
                self,
                name,
                bucket_name=name,
            )
        except:
            ndjson_bucket = s3.Bucket.from_bucket_name(
                self,
                name,
                bucket_name=name,
            )
        return ndjson_bucket
