# covid-data-pipeline

This repo houses docker images and deployment code for producing cloud-optimized
data products for COVID impact analyses and interfaces, such as
https://github.com/NASA-IMPACT/covid-dashboard.

## Requirements

* docker, terraform
* If running python handler code without the docker image, you will need python and python packages:
  * numpy
  * rio-viz
  * netCDF4

## What's here?

* `docker/` includes code and instructions for creating docker images for
  running data conversion, such as NetCDF/HDF to COG. See individual directories
  for more information and run instructions.
* `terraform/` includes terraform files for deploying an AWS Batch Compute
  Environment and corresponding AWS resources for running data conversions. See
  the README in that directory for instructions on deploying AWS infrastructure.
* `scripts/` includes scripts for running and testing data conversion processes.
  See below for examples.

## Scripts

`/scripts/batch/submit-job.sh` submits a NetCDF/HDF to COG conversion job to the AWS
Batch Queue to be picked up by the AWS Batch Compute environment. It assumes:

* You have pushed the [`docker/nc-to-cog`](./docker/nc-to-cog) docker image
  with AWS ECR.

Example:

```bash
$ ./scripts/batch/submit-job.sh OMNO2d_HRM
Executing job nc-to-cog_OMNO2d_HRM_20200516-131654
{
    "jobName": "nc-to-cog_OMNO2d_HRM_20200516-131654",
    "jobId": "6864b575-1c58-447f-85ae-a2a1f9f24b46"
}
```

