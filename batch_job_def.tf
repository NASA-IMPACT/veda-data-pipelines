resource "aws_batch_job_definition" "hdf5_to_cog_batch_job_def" {
  name = "hdf5_to_cog_batch_job_def"
  type = "container"

  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["./run.py"],
    "image": "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/hdf5-to-cog:latest",
    "memory": 2048,
    "vcpus": 2,
    "environment": [
        {"name": "USERNAME", "value": "${var.earthdata_username}"},
        {"name": "PASSWORD", "value": "${var.earthdata_password}"}
    ],
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