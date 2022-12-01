
resource "aws_ecs_cluster" "mwaa_cluster" {
  name = "${var.prefix}-cluster"
}