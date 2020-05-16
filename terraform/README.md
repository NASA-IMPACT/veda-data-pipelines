# Terraform Deployment

This terraform deployment deploys AWS resources detailed in `main.tf` to AWS
using an S3 backend store (currently `s3://covid-eo-data-tf/terraform.tfstate).

This deployment assumes:
* You have the necessary AWS credentials to create the resources in `main.tf` in
  the AWS account associated with your active `AWS_PROFILE`.
* You have pushed the [`docker/nc-to-cog`](../docker/nc-to-cog) docker image to AWS ECR.

```bash
export AWS_PROFILE=xxx
# Copy the example variables.tf file and add appropriate values (e.g. subnets).
cp variables.tf.example variables.tf
terraform init
terraform apply
```

