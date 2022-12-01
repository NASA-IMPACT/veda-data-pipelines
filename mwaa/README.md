# About
This repository provides a Terraform module to provision Amazon Managed Workflows for Apache Airflow (MWAA) environment.
[MWAA](https://aws.amazon.com/managed-workflows-for-apache-airflow)
## Requirements
- Terrraform (v1.3.1 or higher)  [install terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- AWS Account


## How to deploy
```bash
$cp .env.example .env
# Fill values for the environments variables

# Init terraform modules
$bash deploy.sh .env init

# Deploy
$bash deploy.sh .env deploy
```


* Advantages of using AIRFLOW vs State Machines
  * Monitor the logs as the tasks are running
  * No need to tie multiple DAGs with SQS queues (less development)
  * No need to create an API gateway to run a DAG
  * Developers can just start implementing the DAG instead of worrying about the infrastructure
  * Can be used for multiple cloud provider
  * Can be tested locally
  * No need to worry about scalability 
  * No need to create cloudwatch rules and schedules (already included)