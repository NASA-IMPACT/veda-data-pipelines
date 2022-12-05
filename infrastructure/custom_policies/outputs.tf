output "custom_policy_arns_map" {
  value = {
    "custom_policy_arns"= aws_iam_policy.read_data.arn
  }

}