provider "aws" {
  region  = "us-east-1"
}

terraform {
  backend "s3" {
    bucket = "covid-eo-data-tf"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "ecs_instance_role" {
  name = "ecs_instance_role"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
        "Service": "ec2.amazonaws.com"
        }
    }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_instance_role" {
  role       = "${aws_iam_role.ecs_instance_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ecs_s3_policy_attachment" {
  role       = "${aws_iam_role.ecs_instance_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_instance_profile" "ecs_instance_role" {
  name = "ecs_instance_role"
  role = "${aws_iam_role.ecs_instance_role.name}"
}

resource "aws_iam_role" "aws_batch_service_role" {
  name = "aws_batch_service_role"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
        "Service": "batch.amazonaws.com"
        }
    }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "aws_batch_service_role" {
  role       = "${aws_iam_role.aws_batch_service_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

resource "aws_security_group" "batch_security_group" {
  name = "aws_batch_compute_environment_security_group"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_launch_template" "batch_compute_launch_template" {
  name = "batch_compute_launch_template"

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = 210
    }
  }
}

resource "aws_batch_compute_environment" "covid_data_pipeline" {
  compute_environment_name = "covid_data_pipeline"

  compute_resources {
    image_id = "ami-0aee8ced190c05726"

    instance_role = "${aws_iam_instance_profile.ecs_instance_role.arn}"
    launch_template {
      launch_template_id = "${aws_launch_template.batch_compute_launch_template.id}"
    }

    ec2_key_pair = "devseed-aimee"

    instance_type = [
      "optimal",
    ]

    max_vcpus = 256
    desired_vcpus = 0
    min_vcpus = 0

    security_group_ids = [
      "${aws_security_group.batch_security_group.id}",
    ]

    subnets = "${var.subnets}"

    type = "EC2"
  }

  service_role = "${aws_iam_role.aws_batch_service_role.arn}"
  type         = "MANAGED"
  depends_on   = ["aws_iam_role_policy_attachment.aws_batch_service_role"]
}

resource "aws_batch_job_definition" "omno2_to_cog_batch_job_def" {
  name = "omno2_to_cog_batch_job_def"
  type = "container"

  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["./run-cog-convert.sh"],
    "image": "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-1.amazonaws.com/omno2-to-cog:latest",
    "memory": 1024,
    "vcpus": 1,
    "environment": [],
    "ulimits": [
      {
        "hardLimit": 1024,
        "name": "nofile",
        "softLimit": 1024
      }
    ]
}
CONTAINER_PROPERTIES
}

resource "aws_batch_job_definition" "hdf4_to_cog_batch_job_def" {
  name = "hdf4_to_cog_batch_job_def"
  type = "container"

  container_properties = <<CONTAINER_PROPERTIES
{
    "command": ["./run.sh"],
    "image": "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-1.amazonaws.com/hdf4-to-cog:latest",
    "memory": 32000,
    "vcpus": 16,
    "environment": []
}
CONTAINER_PROPERTIES
}

resource "aws_batch_job_queue" "default_job_queue" {
  name                 = "default-job-queue"
  state                = "ENABLED"
  priority             = 1
  compute_environments = ["${aws_batch_compute_environment.covid_data_pipeline.arn}"]
}

