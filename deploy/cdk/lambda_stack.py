from aws_cdk import (
    core,
    aws_lambda,
    aws_lambda_python,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_stepfunctions as stepfunctions,
)

import config
from cdk.iam_policies import IamPolicies


class LambdaStack(core.Stack):
    def __init__(self, app, construct_id, database_vpc, **kwargs) -> None:
        super().__init__(app, construct_id, **kwargs)
        self.construct_id = construct_id
        # Define all lambdas
        # Discovers files from s3 bucket
        self.s3_discovery_lambda = self._lambda(
            f"{construct_id}-s3-discovery-fn", "../lambdas/s3-discovery"
        )

        # Discovers files from cmr
        self.cmr_discovery_lambda = self._lambda(
            f"{construct_id}-cmr-discovery-fn", "../lambdas/cmr-query"
        )

        # Cogify files
        self.cogify_lambda = self._lambda(
            f"{construct_id}-cogify-fn",
            "../lambdas/cogify",
            env={
                "EARTHDATA_USERNAME": config.EARTHDATA_USERNAME,
                "EARTHDATA_PASSWORD": config.EARTHDATA_PASSWORD,
            },
        )

        self.lambda_sg = self._lambda_sg_for_db(construct_id, database_vpc)

        # Proxy lambda to trigger cogify step function
        self.trigger_cogify_lambda = self._python_lambda(
            f"{construct_id}-trigger-cogify-fn",
            "../lambdas/proxy",
        )

        # Proxy lambda to trigger ingest and publish step function
        self.trigger_ingest_lambda = self._python_lambda(
            f"{construct_id}-trigger-ingest-fn", "../lambdas/proxy"
        )

        # Builds ndjson
        self.build_ndjson_lambda = self._lambda(
            f"{construct_id}-build-ndjson-fn",
            "../lambdas/build-ndjson",
            memory_size=8000,
        )

        # Submit STAC lambda
        self.submit_stac_lambda = self._lambda(
            f"{construct_id}-submit-stac-fn",
            "../lambdas/submit-stac",
            memory_size=8000,
            env={
                "COGNITO_APP_SECRET": config.COGNITO_APP_SECRET,
                "STAC_INGESTOR_API_URL": config.COGNITO_APP_SECRET,
            },
            vpc=database_vpc,
            security_groups=[self._lambda_sg],
        )

        ndjson_bucket = self._bucket(f"{construct_id}-ndjson-bucket")
        ndjson_bucket.grant_read_write(self.build_ndjson_lambda.role)
        ndjson_bucket.grant_read(self.submit_stac_lambda.role)

        self.build_ndjson_lambda.add_environment("BUCKET", ndjson_bucket.bucket_name)
        self.submit_stac_lambda.add_environment("BUCKET", ndjson_bucket.bucket_name)

        if config.ENV in ["stage", "prod"]:
            # Transfer data to MCP bucket
            data_transfer_role = iam.Role(
                self,
                f"{construct_id}-data-transfer-role",
                role_name=f"{construct_id}-data-transfer-role",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                description="Role to write to MCP bucket",
            )
            data_transfer_role.add_to_policy(
                iam.PolicyStatement(
                    resources=[config.MCP_ROLE_ARN],
                    actions=["sts:AssumeRole"],
                )
            )
            self.data_transfer_lambda = self._python_lambda(
                f"{construct_id}-data-transfer-fn",
                "../lambdas/data-transfer",
                env={
                    "BUCKET": config.MCP_BUCKETS.get(config.ENV, ""),
                    "MCP_ROLE_ARN": config.MCP_ROLE_ARN,
                },
                role=data_transfer_role,
            )

        self.give_permissions()

    def _lambda(
        self,
        name,
        dir,
        memory_size=1024,
        timeout_seconds=900,
        env=None,
        vpc=None,
        security_groups=None,
        reserved_concurrent_executions=None,
    ):
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
            timeout=core.Duration.seconds(timeout_seconds),
            environment=env,
            vpc=vpc,
            security_groups=security_groups,
            reserved_concurrent_executions=reserved_concurrent_executions,
        )

    def _python_lambda(self, name, directory, env=None, timeout_seconds=900, **kwargs):
        return aws_lambda_python.PythonFunction(
            self,
            name,
            function_name=name,
            entry=directory,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="handler.py",
            handler="handler",
            environment=env,
            timeout=core.Duration.seconds(timeout_seconds),
            **kwargs,
        )

    def _lambda_sg_for_db(self, construct_id, database_vpc):
        # Security group for submit-stac lambda
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

    def give_permissions(self):
        self._read_buckets = [config.VEDA_DATA_BUCKET] + config.VEDA_EXTERNAL_BUCKETS
        for bucket in self._read_buckets:
            self.s3_discovery_lambda.add_to_role_policy(
                IamPolicies.bucket_read_access(bucket)
            )
            self.build_ndjson_lambda.add_to_role_policy(
                IamPolicies.bucket_read_access(bucket)
            )
            if data_transfer_lambda := getattr(self, "data_transfer_lambda", None):
                data_transfer_lambda.add_to_role_policy(
                    IamPolicies.bucket_read_access(bucket)
                )
        self.cogify_lambda.add_to_role_policy(
            IamPolicies.bucket_full_access(config.VEDA_DATA_BUCKET)
        )
        if data_transfer_lambda := getattr(self, "data_transfer_lambda", None):
            data_transfer_lambda.add_to_role_policy(
                IamPolicies.bucket_full_access(config.MCP_BUCKETS.get(config.ENV))
            )

        cognito_app_secret = secretsmanager.Secret.from_secret_name_v2(
            self, f"{self.construct_id}-secret", config.COGNITO_APP_SECRET
        )
        cognito_app_secret.grant_read(self.submit_stac_lambda.role)

    def _bucket(self, name):
        return s3.Bucket.from_bucket_name(
            self,
            name,
            bucket_name=name,
        )

    @staticmethod
    def grant_execution_privileges(
        lambda_function: aws_lambda.Function,
        workflow: stepfunctions.StateMachine,
    ):
        workflow.grant_start_execution(lambda_function.grant_principal)
        lambda_function.add_environment("STEP_FUNCTION_ARN", workflow.state_machine_arn)
