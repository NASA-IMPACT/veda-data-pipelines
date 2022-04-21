from aws_cdk import aws_iam

class IamPolicies:
    def __init__(self, bucket_name):
        self._bucket_name = bucket_name

        # ec2_network_access = aws_iam.PolicyStatement(
        #     actions=[
        #         "ec2:CreateNetworkInterface",
        #         "ec2:DescribeNetworkInterfaces",
        #         "ec2:DeleteNetworkInterface",
        #     ],
        #     resources=["*"],
        # )
        # db_write_lambda.add_to_role_policy(ec2_network_access)    
    
    @property
    def read_access(self):
        return aws_iam.PolicyStatement(
            actions=["s3:GetObject", "s3:ListBucket"],
            resources=[f"arn:aws:s3:::{self._bucket_name}*"],
        )

    @property
    def full_access(self):
        return aws_iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject"],
            resources=[f"arn:aws:s3:::{self._bucket_name}/*"],
        )
