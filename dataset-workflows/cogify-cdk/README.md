<h1 align=center>GRDI CDK ETCL Process</h1>

The `cdk.json` file tells the CDK Toolkit how to execute your app (see root of this repo)

The CDK code in this repository currently deploys state machines and the tasks they depend on to discover data, transform that data (into cloud-optimized forms) and publish metadata to a STAC database.

Current tasks included are:

* S3 Discovery Task - Discovers a list files, each one becomes input for a Map iterator.
* Inputs to the Map iterator are submitted to:
    * Generate COG: Creates and writes COG to S3, pass granule ID and S3 location to Stac Generation task
    * STAC Generation: Creates STAC item from COG and posts to STAC database. Credentials are provided to the CDK workflow via environment variables. See `../stac-gen/README.txt` for more details.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## Deploying this stack

`VPC_ID` must be defined as an environment variable to deploy this stack. This is the ID of the VPC which contains the target database.

```
nvm use 14
pip install aws-cdk.aws-stepfunctions-tasks
cdk deploy
```
