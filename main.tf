provider "aws" {
  region  = "us-east-1"
}

terraform {
  backend "s3" {
    bucket = "maap-cloud-optimized-tf"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "null_resource" "put_ssm_parameters" {
  provisioner "local-exec" {
    command = "python ${path.module}/generate-ssm.py"
  }
  triggers = { env_file = filebase64("env.json") }
}
