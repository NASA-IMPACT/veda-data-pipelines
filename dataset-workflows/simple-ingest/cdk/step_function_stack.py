from aws_cdk import (
    core,
    aws_stepfunctions as stepfunctions,
    aws_stepfunctions_tasks as tasks,
)


class StepFunctionStack(core.Stack):
    def __init__(
        self,
        app,
        construct_id,
        lambda_stack,
        **kwargs
    ):
        super().__init__(app, construct_id, **kwargs)

        self.construct_id = construct_id
        lambdas = lambda_stack.lambdas
        s3_discovery_lambda = lambdas["s3_discovery_lambda"]
        cmr_discovery_lambda = lambdas["cmr_discovery_lambda"]
        cogify_lambda = lambdas["cogify_lambda"]
        build_ndjson_lambda = lambdas["build_ndjson_lambda"]
        pgstac_loader_lambda = lambdas["pgstac_loader_lambda"]
        cogify_or_not_lambda = lambdas["cogify_or_not_lambda"]

        cogify_or_not_task = self._lambda_task("Cogify Or Not Task", cogify_or_not_lambda, input_path="$.Payload")
        cmr_discover_task = self._lambda_task("CMR Discover Task", cmr_discovery_lambda).next(cogify_or_not_task)
        s3_discover_task = self._lambda_task("S3 Discover Task", s3_discovery_lambda).next(cogify_or_not_task)
        cogify_task = self._lambda_task("Cogify", cogify_lambda)
        build_ndjson_task = self._lambda_task("Build Ndjson Task", build_ndjson_lambda)
        pgstac_loader_task = self._lambda_task("Write to database Task", pgstac_loader_lambda, input_path="$.Payload")
        discovery_workflow = stepfunctions.Choice(self, "Discovery Choice (CMR or S3)")\
            .when(stepfunctions.Condition.string_equals("$.discovery", "s3"), s3_discover_task)\
            .when(stepfunctions.Condition.string_equals("$.discovery", "cmr"), cmr_discover_task)\
            .otherwise(stepfunctions.Fail(self, "Discovery Type not supported"))

        cogify_workflow = stepfunctions.Map(
            self,
            "Run concurrent cogifications",
            max_concurrency=100,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        ).iterator(cogify_task)

        ingest_and_publish_workflow = build_ndjson_task.next(pgstac_loader_task)

        self._step_functions = {}
        self._step_functions["discovery"] = stepfunctions.StateMachine(
            self, f"{construct_id}-discover-sf", state_machine_name=f"{construct_id}-discover", definition=discovery_workflow
        )

        self._step_functions["cogify"] = stepfunctions.StateMachine(
            self, f"{construct_id}-cogify-sf", state_machine_name=f"{construct_id}-cogify", definition=cogify_workflow
        )

        self._step_functions["publication"] = stepfunctions.StateMachine(
            self, f"{construct_id}-publication-sf", state_machine_name=f"{construct_id}-publication", definition=ingest_and_publish_workflow
        )

    def _lambda_task(self, name, lambda_function, input_path=None):
        return tasks.LambdaInvoke(
            self,
            name,
            lambda_function=lambda_function,
            input_path=input_path,
        )

    @property
    def state_machines(self):
        return self._step_functions

    def get_arns(self, env_vars):
        base_str = f"arn:aws:states:{env_vars.region}:{env_vars.account}:stateMachine:"
        return (
            f"{base_str}{self.construct_id}-cogify",
            f"{base_str}{self.construct_id}-publication"
        )
