import os
from aws_cdk import (
    core,
    aws_iam,
    aws_stepfunctions as stepfunctions,
    aws_lambda,
    aws_stepfunctions_tasks as tasks,
    aws_ec2 as ec2,
)
import config


class CdkStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define all lambdas
        # Discovers files from s3 bucket
        s3_discovery_lambda = self._lambda(f"{construct_id}-s3-discovery-fn", "../../lambdas/s3-discovery")

        # Discovers files from cmr
        cmr_discovery_lambda = self._lambda(f"{construct_id}-cmr-discovery-fn", "../../lambdas/cmr-query")

        # Cogify files
        cogify_lambda = self._lambda(f"{construct_id}-cogify-fn", "../../lambdas/cogify")
        
        # Generates stac item from input
        generate_stac_item_lambda = self._lambda(f"{construct_id}-generate-stac-item-fn", "../../lambdas/stac-gen",
            memory_size=4096, timeout=60
        )

        # Database config
        database_vpc = ec2.Vpc.from_lookup(self, f"{construct_id}-vpc", vpc_id=config.VPC_ID)
        # PGSTAC database SG
        database_security_group = ec2.SecurityGroup.from_security_group_id(self, "SG", config.SECURITY_GROUP_ID)

        lambda_function_security_group = self._lambda_sg_for_db(construct_id, database_vpc)
        # Give lambda permission to write to database
        database_security_group.add_ingress_rule(
            lambda_function_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow pgstac database write access to lambda",
        )

        # Writes stac item to the pgstac database
        db_write_lambda = self._lambda(f"{construct_id}-write-db-fn", "../../lambdas/db-write",
            memory_size=4096,
            timeout=360,
            env={
                "STAC_DB_HOST": os.environ["STAC_DB_HOST"],
                "STAC_DB_USER": os.environ["STAC_DB_USER"],
                "PGPASSWORD": os.environ["PGPASSWORD"]
            },
            vpc=database_vpc,
            security_groups=[lambda_function_security_group]
        )

        # Roles
        bucket = "climatedashboard-data"

        # Provide list and read access to bucket
        s3_discovery_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[f"arn:aws:s3:::{bucket}*"],
            )
        )
        
        # Provide read and write bucket access to generate stac lambda
        full_bucket_access = aws_iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject"],
            resources=[f"arn:aws:s3:::{bucket}/*"],
        )

        generate_stac_item_lambda.add_to_role_policy(full_bucket_access)
        cogify_lambda.add_to_role_policy(full_bucket_access)

        # ec2_network_access = aws_iam.PolicyStatement(
        #     actions=[
        #         "ec2:CreateNetworkInterface",
        #         "ec2:DescribeNetworkInterfaces",
        #         "ec2:DeleteNetworkInterface",
        #     ],
        #     resources=["*"],
        # )
        # db_write_lambda.add_to_role_policy(ec2_network_access)

        self._step_function(construct_id, s3_discovery_lambda, cmr_discovery_lambda, cogify_lambda, generate_stac_item_lambda, db_write_lambda)

    def _lambda(self, name, dir, memory_size=1024, timeout=30, env=None, vpc=None, security_groups=None):
        return aws_lambda.Function(
            self,
            name,
            function_name=name,
            code=aws_lambda.Code.from_asset_image(
                directory=dir,
                file="Dockerfile",
                entrypoint=["/usr/local/bin/python", "-m", "awslambdaric"],
                cmd=["handler.handler"],
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=memory_size,
            timeout=core.Duration.seconds(timeout),
            environment=env,
            vpc=vpc,
            security_groups=security_groups,
        )

    def _lambda_sg_for_db(self, construct_id, database_vpc):
        # Security group for db-write lambda
        lambda_function_security_group = ec2.SecurityGroup(
            self,
            f"{construct_id}-lambda-sg",
            vpc=database_vpc,
            description="fromCloudOptimizedPipelineLambdas",
        )
        lambda_function_security_group.add_egress_rule(
            ec2.Peer.any_ipv4(),
            connection=ec2.Port(protocol=ec2.Protocol("ALL"), string_representation=""),
            description="Allow lambda security group all outbound access",
        )
        return lambda_function_security_group

    def _step_function(self, construct_id, s3_discovery_lambda, cmr_discovery_lambda, cogify_lambda, generate_stac_item_lambda, db_write_lambda):

        def _lambda_task(name, lambda_function, input_path=None):
            return tasks.LambdaInvoke(
                self,
                name,
                lambda_function=lambda_function,
                input_path=input_path,
            )

        cmr_discover_task = _lambda_task("CMR Discover Task", cmr_discovery_lambda)
        s3_discover_task = _lambda_task("S3 Discover Task", s3_discovery_lambda)
        cogify_task = _lambda_task("Cogify", cogify_lambda)
        s3_generate_stac_item_task = _lambda_task("Generate STAC Item Task", generate_stac_item_lambda)
        s3_db_write_task = _lambda_task("DB Write task", db_write_lambda, input_path="$.Payload")


        cogify = stepfunctions.Choice(self, "Cogify?")\
            .when(stepfunctions.Condition.boolean_equals("$.cogify", True), cogify_task)\
            .otherwise(s3_generate_stac_item_task.next(s3_db_write_task))
        
        map_cogify = stepfunctions.Map(
            self,
            "Map STAC Item Generate and Write",
            max_concurrency=10,
            items_path=stepfunctions.JsonPath.string_at("$.Payload"),
        ).iterator(cogify)

        s3_wflow_definition = stepfunctions.Choice(self, "Discovery Choice (CMR or S3)").when(stepfunctions.Condition.string_equals("$.discovery", "s3"), s3_discover_task.next(map_cogify)).when(stepfunctions.Condition.string_equals("$.discovery", "cmr"), cmr_discover_task.next(map_cogify)).otherwise(stepfunctions.Fail(self, "Discovery Type not supported"))

        stepfunctions.StateMachine(
            self, f"{construct_id}-StateMachine", state_machine_name=f"{construct_id}-StateMachine" , definition=s3_wflow_definition
        )
