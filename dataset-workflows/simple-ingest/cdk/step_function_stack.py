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

        lambdas = lambda_stack.lambdas
        s3_discovery_lambda = lambdas["s3_discovery_lambda"]
        cmr_discovery_lambda = lambdas["cmr_discovery_lambda"]
        cogify_lambda = lambdas["cogify_lambda"]
        generate_stac_item_lambda = lambdas["generate_stac_item_lambda"]
        db_write_lambda = lambdas["db_write_lambda"]

        cmr_discover_task = self._lambda_task("CMR Discover Task", cmr_discovery_lambda)
        s3_discover_task = self._lambda_task("S3 Discover Task", s3_discovery_lambda)
        cogify_task = self._lambda_task("Cogify", cogify_lambda)
        generate_stac_item_task = self._lambda_task("Generate STAC Item Task", generate_stac_item_lambda)
        s3_db_write_task = self._lambda_task("DB Write task", db_write_lambda, input_path="$.Payload")

        generate_and_write_stac_item_task = generate_stac_item_task.next(s3_db_write_task)
        cogify = stepfunctions.Choice(self, "Cogify?")\
            .when(stepfunctions.Condition.boolean_equals("$.cogify", True), cogify_task.next(generate_and_write_stac_item_task))\
            .otherwise(generate_and_write_stac_item_task)
        
        map_cogify = stepfunctions.Map(
            self,
            "Map STAC Item Generate and Write",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        ).iterator(cogify)

        queue = stepfunctions.Choice(self, "Queue?")\
            .when(stepfunctions.Condition.boolean_equals("$.queue", True), stepfunctions.Succeed(self, "Queued."))\
            .otherwise(map_cogify)

        s3_wflow_definition = stepfunctions.Choice(self, "Discovery Choice (CMR or S3)")\
            .when(stepfunctions.Condition.string_equals("$.discovery", "s3"), s3_discover_task.next(queue))\
            .when(stepfunctions.Condition.string_equals("$.discovery", "cmr"), cmr_discover_task.next(queue))\
            .otherwise(stepfunctions.Fail(self, "Discovery Type not supported"))

        stepfunctions.StateMachine(
            self, f"{construct_id}-state-machine", state_machine_name=f"{construct_id}state-machine" , definition=s3_wflow_definition
        )

    def _lambda_task(self, name, lambda_function, input_path=None):
        return tasks.LambdaInvoke(
            self,
            name,
            lambda_function=lambda_function,
            input_path=input_path,
        )
