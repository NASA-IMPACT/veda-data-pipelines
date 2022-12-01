
module "veda_ecs_cluster" {
  source = "./ecs"
  prefix = var.prefix
}

module "custom_policy" {
  source          = "./custom_policies"
  prefix          = var.prefix
  account_id      = data.aws_caller_identity.current.account_id
  aws_log_group_name = "${var.prefix}-mwaalogs"
  aws_log_stream_name = "${var.prefix}-stream-mwaalogs"
  cluster_name = module.veda_ecs_cluster.cluster_name
  assume_role_arn = var.assume_role_arn
  region = local.aws_region
}

module "mwaa" {
  source                           = "https://github.com/amarouane-ABDELHAK/mwaa_tf_module/releases/download/v1.1.1/mwaa_tf_module.zip"
  prefix                           = var.prefix
  vpc_id                           = var.vpc_id
  #iam_role_additional_arn_policies = merge(module.custom_policy.custom_policy_arns_map)
  permissions_boundary_arn         = var.iam_role_permissions_boundary
  subnet_tagname = var.subnet_tagname
  local_requirement_file_path = "${path.module}/../requirements.txt"
  local_dag_folder = "${path.module}/../dags/"
}