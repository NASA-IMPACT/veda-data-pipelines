import os
from aws_cdk import (
    core,
    aws_lambda,
    aws_ec2 as ec2,
)

import config


class LambdaStack(core.Stack):
    def __init__(self, app, construct_id, database_vpc, iam_stack, **kwargs) -> None:
        super().__init__(app, construct_id, **kwargs)
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
            security_groups=[self._lambda_sg]
        )

        # Builds ndjson
        build_ndjson_lambda = self._lambda(f"{construct_id}-build-ndjson-fn", "../../lambdas/ndjson-builder",
            memory_size=8000,
            timeout=600
        )

        # PGStac loader
        pgstac_loader_lambda = self._lambda(f"{construct_id}-loader-fn", "../../lambdas/pgstac-loader",
            memory_size=8000,
            timeout=600,
            env={
                "SECRET_NAME": config.SECRET_NAME
            },
            reserved_concurrent_executions=3,
            vpc=database_vpc,
            security_groups=[self._lambda_sg],
        )

        self._lambdas = {
            "s3_discovery_lambda": s3_discovery_lambda,
            "cmr_discovery_lambda": cmr_discovery_lambda,
            "cogify_lambda": cogify_lambda,
            "generate_stac_item_lambda": generate_stac_item_lambda,
            "db_write_lambda": db_write_lambda,
            "build_ndjson_lambda": build_ndjson_lambda,
            "pgstac_loader_lambda": pgstac_loader_lambda,
        }

        self.give_permissions(iam_stack)

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

    def give_permissions(self, iam_stack):
        self._lambdas["s3_discovery_lambda"].add_to_role_policy(iam_stack.read_access)
        self._lambdas["generate_stac_item_lambda"].add_to_role_policy(iam_stack.full_access)
        self._lambdas["cogify_lambda"].add_to_role_policy(iam_stack.full_access)
