from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct
import json

from config import Config


class DataPipelineUtilStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)
        # rebuild config as dict
        env_dict = {
            "ENV": config.ENV,
            "OIDC_PROVIDER_ARN": config.OIDC_PROVIDER_ARN,
            "OIDC_REPO_ID": config.OIDC_REPO_ID,
            "COGNITO_APP_SECRET": config.COGNITO_APP_SECRET,
            "STAC_INGESTOR_URL": config.STAC_INGESTOR_URL,
            "EXTERNAL_ROLE_ARN": config.EXTERNAL_ROLE_ARN,
            "MCP_BUCKETS": config.MCP_BUCKETS,
            "EARTHDATA_USERNAME": config.EARTHDATA_USERNAME,
            "EARTHDATA_PASSWORD": config.EARTHDATA_PASSWORD,
            "SECRET_NAME": config.SECRET_NAME,
            "VECTOR_VPC_ID": config.VECTOR_VPC_ID,
            "VECTOR_SECURITY_GROUP": config.VECTOR_SECURITY_GROUP,
            "VECTOR_SECRET_NAME": config.VECTOR_SECRET_NAME,
        }

        env_secret = self.build_env_secret(config.ENV, env_dict)
        secret_arn: str = env_secret.secret_arn

        if config.OIDC_PROVIDER_ARN:
            self.build_oidc(
                config.OIDC_PROVIDER_ARN,
                config.OIDC_REPO_ID,
                secret_arn,
                config.ENV,
            )

    def build_oidc(
        self, oidc_provider_arn: str, oidc_repo_id: str, secret_arn: str, stage: str
    ):
        # Create an IAM OIDC provider for the specified provider ARN
        oidc_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self, "OIDCProvider", oidc_provider_arn
        )
        # create IAM role for provider access from specified repo
        # the role should allow a github action in that repo
        # to deploy resources (TODO) and read a secret
        oidc_role = iam.Role(
            self,
            f"data-pipelines-oidc-role-{stage}",
            assumed_by=iam.WebIdentityPrincipal(
                oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        f"{oidc_provider.open_id_connect_provider_issuer}:sub": f"repo:{oidc_repo_id}"
                    }
                },
            ),
        )
        oidc_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRoleWithWebIdentity"],
                resources=[oidc_provider_arn],
            )
        )
        # Create an IAM policy statement that allows getting the secret value
        get_secret_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["secretsmanager:GetSecretValue"],
            resources=[secret_arn],
        )

        # NOTE - this can be refined later using cloudtrail to limit access to specific actions
        # enables cdk deployment from github action
        deploy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sts:AssumeRole"],
            resources=["arn:aws:iam::*:role/cdk-*"],
        )

        oidc_policy = iam.Policy(
            self,
            f"data-pipelines-oidc-policy-{stage}",
            policy_name=f"data-pipelines-oidc-policy-{stage}",
            roles=[oidc_role],
            statements=[get_secret_statement, deploy_statement],
        )
        return oidc_role, oidc_policy, oidc_provider

    def build_env_secret(self, stage: str, env_config: dict) -> secretsmanager.ISecret:
        # create secret to store environment variables
        return secretsmanager.Secret(
            self,
            f"data-pipelines-env-secret-{stage}",
            secret_name=f"data-pipelines-env-secret-{stage}",
            description="Contains env vars used for deployment of veda-data-pipelines",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(env_config),
                generate_string_key="password",
                exclude_punctuation=True,
            ),
        )
