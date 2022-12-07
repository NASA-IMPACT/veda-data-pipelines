variable "prefix" {}

variable "region" {}

variable "cluster_name" {}

variable "account_id" {}

variable "aws_log_group_name" {}

variable "aws_log_stream_name" {}

variable "assume_role_write_arn" {
  description = "Assume role ARN for writing to MCP"
}

variable "assume_role_read_arn" {
  description = "Assume role ARN for reading from MCP"
}
