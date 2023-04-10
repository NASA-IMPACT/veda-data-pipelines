from aws_cdk import (
    core,
    aws_lambda,
    aws_lambda_python,
    aws_iam as iam,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
)

import config


class LambdaStack(core.Stack):
    def __init__(self, app, construct_id, **kwargs) -> None:
        super().__init__(app, construct_id, **kwargs)
        self.construct_id = construct_id

        # external role
        external_role = iam.Role(
            self,
            f"delta-backend-staging-{config.ENV}-external-role",
            role_name=f"delta-backend-staging-{config.ENV}-external-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role to write to external bucket",
        )
        external_role.attach_inline_policy(
            iam.Policy(
                self,
                "Policy",
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "logs:PutLogEvents",
                            "logs:DescribeLogStreams",
                            "logs:CreateLogStream",
                            "logs:CreateLogGroup",
                        ],
                        resources=["*"],
                    ),
                    iam.PolicyStatement(
                        resources=[config.DATA_MANAGEMENT_ROLE_ARN],
                        actions=["sts:AssumeRole"],
                    ),
                ],
            )
        )
        external_role.add_to_policy(
            iam.PolicyStatement(
                resources=[config.DATA_MANAGEMENT_ROLE_ARN],
                actions=["sts:AssumeRole"],
            )
        )

        # Define all lambdas
        # Discovers files from s3 bucket
        self.s3_discovery_lambda = self._lambda(
            f"{construct_id}-s3-discovery-fn",
            "../lambdas/s3-discovery",
            role=external_role,
            env={
                "BUCKET": config.MCP_BUCKETS.get(config.ENV, ""),
                "DATA_MANAGEMENT_ROLE_ARN": config.DATA_MANAGEMENT_ROLE_ARN,
            },
        )

        # Discovers files from cmr
        self.cmr_discovery_lambda = self._lambda(
            f"{construct_id}-cmr-discovery-fn",
            "../lambdas/cmr-query",
            env={"CMR_API_URL": config.CMR_API_URL},
        )

        # Discovers files from cmr
        self.inventory_lambda = self._lambda(
            f"{construct_id}-inventory-fn",
            "../lambdas/inventory",
            role=external_role,
            env={
                "BUCKET": config.MCP_BUCKETS.get(config.ENV, ""),
                "DATA_MANAGEMENT_ROLE_ARN": config.DATA_MANAGEMENT_ROLE_ARN,
            },
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

        # Proxy lambda to trigger discovery step function
        self.trigger_discovery_lambda = self._python_lambda(
            f"{construct_id}-trigger-discover-fn",
            "../lambdas/discovery-trigger",
        )

        # Proxy lambda to trigger cogify step function
        self.trigger_cogify_lambda = self._python_lambda(
            f"{construct_id}-trigger-cogify-fn",
            "../lambdas/proxy",
        )

        # Proxy lambda to trigger ingest and publish step function
        self.trigger_ingest_lambda = self._python_lambda(
            f"{construct_id}-trigger-ingest-fn", "../lambdas/proxy"
        )

        # Builds stac
        self.build_stac_lambda = self._lambda(
            f"{construct_id}-build-stac-fn",
            "../lambdas/build-stac",
            memory_size=1024,
            role=external_role,
            env={
                "DATA_MANAGEMENT_ROLE_ARN": config.DATA_MANAGEMENT_ROLE_ARN,
                "CMR_API_URL": config.CMR_API_URL,
            },
        )

        # Submit STAC lambda
        self.submit_stac_lambda = self._lambda(
            f"{construct_id}-submit-stac-fn",
            "../lambdas/submit-stac",
            memory_size=1024,
            env={
                "COGNITO_APP_SECRET": config.COGNITO_APP_SECRET,
                "STAC_INGESTOR_API_URL": config.STAC_INGESTOR_API_URL,
            },
        )

        # Transfer data to MCP bucket
        self.data_transfer_lambda = self._python_lambda(
            f"{construct_id}-data-transfer-fn",
            "../lambdas/data-transfer",
            env={
                "BUCKET": config.MCP_BUCKETS.get(
                    config.ENV, config.MCP_BUCKETS.get("stage")
                ),
                "USER_SHARED_BUCKET": config.USER_SHARED_BUCKET,
                "DATA_MANAGEMENT_ROLE_ARN": config.DATA_MANAGEMENT_ROLE_ARN,
            },
            role=external_role,
        )

        ndjson_bucket = self._bucket(f"{construct_id}-ndjson-bucket")
        ndjson_bucket.grant_read_write(self.build_stac_lambda.role)
        ndjson_bucket.grant_read(self.submit_stac_lambda.role)

        self.build_stac_lambda.add_environment("BUCKET", ndjson_bucket.bucket_name)
        self.submit_stac_lambda.add_environment("BUCKET", ndjson_bucket.bucket_name)

        self.give_permissions()

    def _lambda(
        self,
        name,
        dir,
        memory_size=1024,
        timeout_seconds=900,
        env=None,
        reserved_concurrent_executions=None,
        **kwargs,
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
            reserved_concurrent_executions=reserved_concurrent_executions,
            **kwargs,
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

    def give_permissions(self):
        internal_bucket = self._bucket(config.VEDA_DATA_BUCKET)
        internal_bucket.grant_read_write(self.cogify_lambda.role)

        mcp_bucket = self._bucket(
            config.MCP_BUCKETS.get(config.ENV, config.MCP_BUCKETS.get("stage"))
        )

        external_buckets = [
            self._bucket(bucket) for bucket in config.VEDA_EXTERNAL_BUCKETS
        ]

        for bucket in [internal_bucket, mcp_bucket, *external_buckets]:
            bucket.grant_read(self.s3_discovery_lambda.role)
            bucket.grant_read(self.build_stac_lambda.role)
            bucket.grant_read(self.data_transfer_lambda.role)

        mcp_bucket.grant_read_write(self.data_transfer_lambda)

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
        workflow_arn: str,
    ):
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[workflow_arn],
            )
        )
        lambda_function.add_environment("STEP_FUNCTION_ARN", workflow_arn)
