# cloud-optimized-data-pipelines

This repo houses docker images and deployment code for producing cloud-optimized
data products and STAC metadata for interfaces such as https://github.com/NASA-IMPACT/delta-ui.

# Requirements

## Docker

See https://docs.docker.com/get-docker/

## CDK

https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html

```bash
nvm use 14
npm install cdk
pip install aws-cdk.aws-stepfunctions-tasks
```

# What's here?

## Dataset Worfklows

The `dataset-workflows/` directory includes pre-defined workflows for data ingest, processing and publication. Each dataset will have it's own workflow which should be documented and repeatable for other developers. Dataset workflows fall into 2 categories:

* Manual: Small, one time ingests (100 files or less) may be processed manually. Example: Black Marble Nightlights data for Hurricanes Ida and Maria.
* Cloud:
    * Large scale ingests will require cloud resources for monitoring, scaling and long-running processes. Example: HLS.
    * Small scale ingests which are ongoing or require automation. Example: Facebook COG generation triggered by new data in `s3://dataforgood-fb-data/`

Each dataset has it's own directory in `dataset-workflows` with documentation on how data ingest and publish runs. Optionally, datasets may have suffixes for the tool used to run the ingest and publish, for example `dataset-workflows/hls-cdk` would include cdk for deploying the HLS pipeline for publishing HLS STAC records.

## Lambdas

The `lambdas/` subdirectory includes lambda code for composing a dataset workflow. Each dataset is expected to have slightly different needs when it comes to data discovery, processing, and publication. These lambda functions should be re-usable across datasets

* `cogify` includes code and Dockerfiles for
  running data conversion to COG, such as NetCDF/HDF5 to COG. 
  
* `cmr-query` includes code and Dockerfiles for discovering HDF5 files from NASA CMR.
  
* `s3-discovery` includes code and Dockerfiles for discovering arbitrary files from an S3 location.
  
* `stac-gen` includes code and Dockerfiles for generating STAC items from a COG using `rio-stac`. Can optionally query CMR for metadata or parse metadata from filenames with provided regex.

* `pgstac-loader` generates multiple records from a ndjson file.
  
See individual directories for more information and run instructions.


