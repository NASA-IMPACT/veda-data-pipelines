
# Required variables
variable "subnet_tagname" {
  description = "Private subnet tagname to use for MWAA"
}
variable "vpc_id" {
  description = "Account VPC to use"
}

variable "prefix" {
  description = "Deployment prefix"
}

variable "iam_role_permissions_boundary" {
  description = "Permission boundaries"
}

variable "assume_role_arn" {
  description = "Assume role ARN from MCP"
}
# Optional variables

variable "aws_profile" {
  description = "AWS profile"
  default = null
}
variable "aws_region" {
  default = "us-west-2"
}

variable "stage" {
  default = "dev"
}