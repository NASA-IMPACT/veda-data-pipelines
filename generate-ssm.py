import json
import boto3
import sys

envs = json.loads(open('env.json', 'r').read())
envs_prefix = open('terraform.tfvars', 'r')
vars = {}
f = open('terraform.tfvars', 'r')
lines = [line.split("=") for line in f.read().split("\n")]
for var in lines:
    vars[var[0].strip().strip("\"\'")] = var[1].strip().strip("\"\'") if len(var) > 1 else None
ssm_prefix = vars['deployment_prefix']
ssm = boto3.client('ssm')
print(f"Writing parameters to namespace {ssm_prefix}")
for env in envs.items():
    name = env[0]
    value = env[1]
    response = ssm.put_parameter(
        Name=f"/{ssm_prefix}/{name}",
        Value=value,
        Type='SecureString',
        Overwrite=True  
    )
   