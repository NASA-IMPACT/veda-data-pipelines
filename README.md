# cloud-optimized-data-pipelines

This repo houses docker images and deployment code for producing cloud-optimized
data products for analyses and interfaces, such as
https://github.com/NASA-IMPACT/covid-dashboard.

## Requirements

* docker, terraform
* If running python handler code without the docker image, you will need python and python packages:
  * numpy
  * rio-viz
  * netCDF4

## What's here?

* `docker/` includes docker images for
  running data conversion, such as NetCDF/HDF5 to COG. See individual directories
  for more information and run instructions.
* Terraform (all `.tf` files) includes terraform file for deploying an AWS Batch Compute
  Environment and corresponding AWS resources for running data conversions.
