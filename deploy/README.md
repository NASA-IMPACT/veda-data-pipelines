
# CDK for COG and STAC generation pipelines

The `cdk.json` file tells the CDK Toolkit how to execute your app (see root of this repo)

The CDK code in this repository currently deploys state machines and the tasks they depend on to discover data, transform that data (into cloud-optimized forms) and publish metadata to a STAC database.

Current tasks included are:

* CMR Query (Discovery Task) -> Outputs a list of `.he5` files, each one becomes input for a Map iterator.
* Inputs to the Map iterator are submitted to:
  * Generate COG: Creates and writes COG to S3, pass granule ID and S3 location to Stac Generation task
  * STAC Generation: Creates STAC item from COG and posts to STAC database. Credentials are provided to the CDK workflow via environment variables. See `../stac-gen/README.txt` for more details.

To have dates assigned as the temporal extent(s) in the STAC item metadata for a given file, use the following conventions for including a datetime in the filename:

* Date string/s in filename (following the yyyy-mm-dd, yyyy, yyyymm, yyyymmdd format): You can supply dates in any part of the filename followed by `_` in the formats `yyyy-mm-dd`, `yyyy`, `yyyymm`, `yyyymmdd`. Ideally, the dates will be towards the end of the filename. Eg: `1234_BeforeMaria_Stage0_2017-09-19_2017-07-21.tif` will extract start date as `2017-07-21` and end date as `2017-09-19` while disregarding `1234`.
* `datetime_range`: If the `datetime_range` is not provided we just set the `datetime` field in the metadatda using the provided date. However, if `datetime_range` is provided (choice of `month` or `year`) we calculate the `start` and `end` date we need to ingest for the metadata. Eg: `1234_BeforeMaria_Stage0_2017.tif` is the filename, the date is set to `2017-01-01` if `datetime_range` is not provided. If it is set to `month`, `start_datetime` is set to `2017-01-01T00:00:00Z` and `end_datetime` is set to `2017-01-31T00:00:00Z` while also setting `date_time` as null. If `datetime_range` is set to `year`, `start_datetime` is set to `2017-01-01T00:00:00Z` and `end_datetime` is set to `2017-12-31T00:00:00Z` while also setting `date_time` as null.

## Useful commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

Enjoy!
