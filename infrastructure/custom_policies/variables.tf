variable "prefix" {}

variable "region" {}

variable "cluster_name" {}

variable "account_id" {}

variable "aws_log_group_name" {}

variable "aws_log_stream_name" {}
variable "assume_role_arn" {
  description = "Assume role ARN from MCP"
}