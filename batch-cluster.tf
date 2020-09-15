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
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ecs_s3_policy_attachment" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_instance_profile" "ecs_instance_role" {
  name = "ecs_instance_role"
  role = aws_iam_role.ecs_instance_role.name
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
  role       = aws_iam_role.aws_batch_service_role.name
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
  name = "batch_launch_template"

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      // modify as needed - some jobs which mosaic many files need more storage space
      volume_size = var.batch_ec2_volume_size
    }
  }
}

data "aws_ami" "batch_ami" {
  owners           = ["amazon"]
  most_recent      = true

  filter {
    name   = "name"
    values = ["amzn2-ami-ecs-hvm-2*x86_64-ebs"]
  }
}

resource "aws_batch_compute_environment" "cloud_optimized_pipeline" {
  compute_environment_name = "cloud-optimized-batch-compute"

  compute_resources {
    image_id = data.aws_ami.batch_ami.id

    instance_role = aws_iam_instance_profile.ecs_instance_role.arn
    launch_template {
      launch_template_id = aws_launch_template.batch_compute_launch_template.id
    }

    instance_type = [
      // Modify this to something like c4.8xlarge if you need to match max vCPUs
      // to a specific number of instances, for example if you want to ensure no
      // instances run more than 20 concurrent web requests.
      // This would also correspond to a job definition - the job definition
      // vCPU requirements will indicate how many instances should be launched
      // for AWS Batch to complete a given set of queued jobs.
      "optimal",
    ]

    max_vcpus = 1440
    desired_vcpus = 16
    min_vcpus = 12

    security_group_ids = [ aws_security_group.batch_security_group.id ]

    subnets = var.subnet_ids

    type = "EC2"
  }

  service_role = aws_iam_role.aws_batch_service_role.arn
  type         = "MANAGED"
  depends_on   = [aws_iam_role_policy_attachment.aws_batch_service_role]
}

resource "aws_batch_job_queue" "default_job_queue" {
  name                 = "default-job-queue"
  state                = "ENABLED"
  priority             = 1
  compute_environments = [aws_batch_compute_environment.cloud_optimized_pipeline.arn]
}
