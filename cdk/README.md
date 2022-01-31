
# CDK for COG and STAC generation pipelines

The `cdk.json` file tells the CDK Toolkit how to execute your app (see root of this repo)

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

This workflow defines a state machine which links together the Lamda tasks defined in this repo.

CMR Query (Discovery Task) -> Outputs a list of `.he5` files, each one becomes input for a Map iterator.

Map iterator:
Generate COG -> Write output to S3, pass granule ID and S3 location to Stac Generation task
STAC Generation -> Create STAC item from COG and post to database, provided to CDK workflow via environment variables (see `../stac-gen/README.txt`)

