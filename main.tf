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
