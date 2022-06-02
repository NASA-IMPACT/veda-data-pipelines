from aws_cdk import aws_iam

class IamPolicies:
    def __init__(self):
        pass
    
    @staticmethod
    def bucket_read_access(bucket_name):
        return aws_iam.PolicyStatement(
            actions=["s3:GetObject", "s3:ListBucket"],
            resources=[f"arn:aws:s3:::{bucket_name}*"],
        )

    @staticmethod
    def bucket_full_access(bucket_name):
        return aws_iam.PolicyStatement(
            actions=["s3:ListBucket", "s3:GetObject", "s3:PutObject"],
            resources=[f"arn:aws:s3:::{bucket_name}*"],
        )

    @staticmethod
    def stepfunction_start_execution_access(state_machine_arn):
        return aws_iam.PolicyStatement(
            actions=["states:StartExecution"],
            resources=[state_machine_arn],
        )
