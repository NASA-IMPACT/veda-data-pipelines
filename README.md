# cloud-optimized-data-pipelines

This repo houses docker images and deployment code for producing cloud-optimized
data products for analyses and interfaces, such as
https://github.com/NASA-IMPACT/covid-dashboard.

## Requirements

* docker, cdk

```bash
nvm use 14
npm install cdk
pip install aws-cdk.aws-stepfunctions-tasks
```

## What's here?

* `cogify/` includes code and Dockerfiles for
  running data conversion to COG, such as NetCDF/HDF5 to COG. See individual directories
  for more information and run instructions.
* `cdk/` includes cdk for deploying pipelines for automating generation of cloud-optimized geotiffs in AWS.


