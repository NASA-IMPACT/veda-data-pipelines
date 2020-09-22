import json
import boto3
import os
import sys

envs = json.loads(open('env.json', 'r').read())
aws_account_id = os.environ.get('AWS_ACCOUNT_ID')
aws_region = os.environ.get('AWS_REGION') or 'us-east-1'
ssm = boto3.client('ssm')

for env in envs.items():
    name = env[0]
    value = env[1]
    response = ssm.put_parameter(
        Name=f"/cloud-optimized-dp/{name}",
        Value=value,
        Type='SecureString',
        Overwrite=True  
    )
   