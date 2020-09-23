import json
import boto3
import sys

envs = json.loads(open('env.json', 'r').read())
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
   