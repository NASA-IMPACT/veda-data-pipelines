# cloud-optimized-data-pipelines

This repo houses function code and deployment code for producing cloud-optimized
data products and STAC metadata for interfaces such as https://github.com/NASA-IMPACT/delta-ui.

## Requirements

### Docker

See [get-docker](https://docs.docker.com/get-docker/)

### AWS CDK

See [cdk-getting-started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)

```bash
nvm install 17.3.0
nvm use 17.3.0
npm install -g aws-cdk
```

### Poetry

See [poetry-landing-page](https://pypi.org/project/poetry/)

```bash
pip install poetry
```

## Deployment

This project uses AWS CDK to deploy AWS resources to the cloud.

### Make sure the following environment variables are set

```bash
VPC_ID="<vpc-xxxxxxx>"
SECURITY_GROUP_ID="sg-xxxxxxxx"
ENV="<dev/stage/prod>"
SECRET_NAME="<secret-name-for-pgstac-access>"
APP_NAME="delta-simple-ingest"
```

**Note:** You can use the handy `env.sample.sh` script to set these variables. Just rename the file to `env.sh` and populate it with appropriate values. Then run the following commands:

```bash
chmod +x env.sh
source env.sh <dev/stage>
```

> If anything other than dev/stage is provided as the env, the dev credentials are used (for now).

## To deploy

### Using poetry

```bash
# deploy
poetry run deploy

# destroy
poetry run destroy
```

### Else

1. Go to `deploy/` directory
2. Create a virtual environment with `python -m venv venv`
3. Activate the virtual environment with `source venv/bin/activate`
4. Install the requirements with `pip install -r requirements.txt`
5. Run `cdk deploy --all`
6. Useful: `cdk destroy --all` to destroy the infrastructure
