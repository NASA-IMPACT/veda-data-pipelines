# veda-data-pipelines

This repo houses function code and deployment code for producing cloud-optimized
data products and STAC metadata for interfaces such as https://github.com/NASA-IMPACT/delta-ui.

## Requirements

### Docker

See [get-docker](https://docs.docker.com/get-docker/)

### Terraform 

See [terraform-getting-started](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

### AWS CLI

See [getting-started-install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### Poetry

See [poetry-landing-page](https://pypi.org/project/poetry/)

```bash
pip install poetry
```

## Deployment

This project uses Terraform modules to deploy Apache Airflow and related AWS resources using Amazon's managed Airflow provider.

### Make sure that environment variables are set

[.env.example`](./.env.example) contains the environment variables which are necessary to deploy. Copy this file and update its contents with actual values. The deploy script will `source` and use this file during deployment when provided through the command line:

```bash
# Copy .env.example to a new file
$cp .env.example .env
# Fill values for the environments variables

# Init terraform modules
$bash ./scripts/deploy.sh .env <<< init

# Deploy
$bash ./scripts/deploy.sh .env <<< deploy
```

**Note:** Be careful not to check in `.env` (or whatever you called your env file) when committing work.

# License
This project is licensed under **Apache 2**, see the [LICENSE](LICENSE) file for more details.

