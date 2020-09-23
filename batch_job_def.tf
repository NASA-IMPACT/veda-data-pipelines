resource "aws_batch_job_definition" "hdf5_to_cog_batch_job_def" {
  name = "hdf5_to_cog_batch_job_def"
  type = "container"

  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["python","run.py","-c","GPM_3IMERGDF","-f","https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.06/2000/06/3B-DAY.MS.MRG.3IMERG.20000601-S000000-E235959.V06.nc4"],
    "image": "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/hdf5-to-cog:latest",
    "memory": 2048,
    "vcpus": 2,
    "environment": [{
      "name": "SSM_PREFIX",
      "value": ${var.deployment_prefix}
    }],
    "logConfiguration": {
      "logDriver": "awslogs",
      "secretOptions": null,
      "options": {
        "awslogs-group": "/batch/hdf5-to-cog",
        "awslogs-region": "${data.aws_region.current.name}",
        "awslogs-stream-prefix": "batch"
      }
    }
}
CONTAINER_PROPERTIES
}