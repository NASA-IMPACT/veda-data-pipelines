# cloud-optimized-data-pipelines

This repo houses function code and deployment code for producing cloud-optimized
data products and STAC metadata for interfaces such as https://github.com/NASA-IMPACT/delta-ui.

## Requirements

### Docker

See https://docs.docker.com/get-docker/

### AWS CDK

See https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html

```bash
nvm use 14
npm install cdk
pip install aws-cdk.aws-stepfunctions-tasks
```

### Poetry

See https://pypi.org/project/poetry/

```bash
pip install poetry
```

## Deployment

This project uses AWS CDK to deploy AWS resources to the cloud.

### Make sure the following environment variables are set:

```bash
VPC_ID="<vpc-xxxxxxx>"
SECURITY_GROUP_ID="sg-xxxxxxxx"
ENV="<dev/stage/prod>"
SECRET_NAME="<secret-name-for-pgstac-access>"
APP_NAME="delta-simple-ingest"
```

#### You can use the handy `env.sh` script to set these variables.

```bash
chmod +x env.sh
./env.sh <dev/stage>
```

> If anything other than dev/stage is provided as the env, the dev credentials are used.

## To deploy:

1. Go to `deploy/` directory
2. Create a virtual environment with `python -m venv venv`
3. Activate the virtual environment with `source venv/bin/activate`
4. Install the requirements with `pip install -r requirements.txt`
5. Run `cdk deploy`
