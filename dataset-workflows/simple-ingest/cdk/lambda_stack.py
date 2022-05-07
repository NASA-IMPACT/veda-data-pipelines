import os
from aws_cdk import (
    core,
    aws_lambda,
    aws_lambda_python,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager
)

import config
from cdk.iam_policies import IamPolicies

class LambdaStack(core.Stack):
    def __init__(self, app, construct_id, database_vpc, **kwargs) -> None:
        super().__init__(app, construct_id, **kwargs)
        self.construct_id = construct_id
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

        self._lambda_sg = self._lambda_sg_for_db(construct_id, database_vpc)

        # Proxy lambda to trigger cogify step function
        cogify_or_not_lambda = self._python_lambda(f"{construct_id}-cogify-or-not-fn", "../../lambdas/cogify-or-not",)

        # Proxy lambda to trigger cogify step function
        trigger_cogify_lambda = self._python_lambda(f"{construct_id}-trigger-cogify-fn", "../../lambdas/proxy",)

        # Proxy lambda to trigger ingest and publish step function
        trigger_ingest_lambda = self._python_lambda(f"{construct_id}-trigger-ingest-fn", "../../lambdas/proxy")

        # Builds ndjson
        build_ndjson_lambda = self._lambda(f"{construct_id}-build-ndjson-fn", "../../lambdas/ndjson-builder",
            memory_size=8000,
            timeout=600
        )

        # PGStac loader
        pgstac_loader_lambda = self._lambda(f"{construct_id}-pgstac-loader-fn", "../../lambdas/pgstac-loader",
            memory_size=8000,
            timeout=600,
            env={
                "SECRET_NAME": config.SECRET_NAME
            },
            vpc=database_vpc,
            security_groups=[self._lambda_sg],
        )

        ndjson_bucket = self._bucket(f"{construct_id}-ndjson-bucket")
        ndjson_bucket.grant_read_write(build_ndjson_lambda.role)
        ndjson_bucket.grant_read(pgstac_loader_lambda.role)

        build_ndjson_lambda.add_environment("BUCKET", ndjson_bucket.bucket_name)
        pgstac_loader_lambda.add_environment("BUCKET", ndjson_bucket.bucket_name)

        self._lambdas = {
            "s3_discovery_lambda": s3_discovery_lambda,
            "cmr_discovery_lambda": cmr_discovery_lambda,
            "cogify_lambda": cogify_lambda,
            "generate_stac_item_lambda": generate_stac_item_lambda,
            "build_ndjson_lambda": build_ndjson_lambda,
            "pgstac_loader_lambda": pgstac_loader_lambda,
            "trigger_cogify_lambda": trigger_cogify_lambda,
            "trigger_ingest_lambda": trigger_ingest_lambda,
            "cogify_or_not_lambda": cogify_or_not_lambda,
        }

        self.give_permissions()

    def _lambda(self, name, dir, memory_size=1024, timeout=30, env=None, vpc=None, security_groups=None, reserved_concurrent_executions=None):
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
            reserved_concurrent_executions=reserved_concurrent_executions,
        )

    def _python_lambda(self, name, directory, env=None):
        return aws_lambda_python.PythonFunction(self, name,
            entry=directory,
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="handler.py",
            handler="handler",
            environment=env
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
    
    @property
    def lambdas(self):
        return self._lambdas

    @property
    def lambda_sg(self):
        return self._lambda_sg

    def give_permissions(self):
        self._lambdas["s3_discovery_lambda"].add_to_role_policy(IamPolicies.bucket_read_access(config.BUCKET_NAME))
        self._lambdas["generate_stac_item_lambda"].add_to_role_policy(IamPolicies.bucket_full_access(config.BUCKET_NAME))
        self._lambdas["cogify_lambda"].add_to_role_policy(IamPolicies.bucket_full_access(config.BUCKET_NAME))
        self._lambdas["build_ndjson_lambda"].add_to_role_policy(IamPolicies.bucket_read_access(config.BUCKET_NAME))

        pgstac_secret = secretsmanager.Secret.from_secret_name_v2(self, f"{self.construct_id}-secret", config.SECRET_NAME)
        pgstac_secret.grant_read(self._lambdas["pgstac_loader_lambda"].role)

    def _bucket(self, name):
        return s3.Bucket.from_bucket_name(
            self,
            name,
            bucket_name=name,
        )
