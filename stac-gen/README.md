Docker to query CMR for granules associated with a given collection and temporal range.

```bash
docker build -t stac-gen .
# Currently runs an example for OMI Ozone
docker run --env STAC_DB_USER=<user> --env STAC_DB_PASSWORD=<pw> --env STAC_DB_HOST=<host> stac-gen python -m handler
```

AWS Provisioning
This Lambda will need to be a part of the same VPC as the STAC_DB_HOST RDS instance which hosts the Postgres database. It also needs access to the Internet to query CMR. Add the following permissions / settings to the Lambda.
- Follow steps [here](https://aws.amazon.com/premiumsupport/knowledge-center/internet-access-lambda-function/) using the VPC that contains the target database. It includes the following steps:
  - Create public and private subnets within target VPC
  - Create an Internet Gateway (enables internet access)
  - Create a NAT gateway
  - Create route tables for private / public subnets (important note: Lambda will randomly select any of the subnets it is associated with at runtime)
  - Add `AWSLambdaVPCAccessExecutionRole` to the Lambda's Execution Rolea
  - Add `ec2:DescribeNetworkInterfaces` and `ec2:CreateNetworkInterface` to the Lambda execution role (not explained in above guide)
  - Add the target VPC to the Lambda's Configuration (can be done on the Lambda console page > configuration > permissions > execution role)
  - Choose the private subnets created above, and the security group that is relevant to the target database
- Add `s3:GetObject` permissions to the Lambda's execution role (this Lambda needs to read `tif` files from `S3`
