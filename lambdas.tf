resource "null_resource" "discover_cmr_granules_build" {
  provisioner "local-exec" {
    command = "cd ${path.module}/lambdas/discover-cmr-granules && make"
  }
  triggers = { lambda_file = filebase64("${path.module}/lambdas/discover-cmr-granules/lambda_function.py") }
}

data "archive_file" "discover-cmr-granules" {
  type        = "zip"
  source_dir  = "${path.module}/lambdas/discover-cmr-granules/package"
  output_path = "${path.module}/lambdas/discover-cmr-granules/package/package.zip"
}

resource "aws_lambda_function" "discover-cmr-granules" {
  function_name = "discover_cmr_granules"
  filename      = data.archive_file.discover-cmr-granules.output_path
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  timeout       = 300

  source_code_hash = data.archive_file.discover-cmr-granules.output_base64sha256
  role = var.lambda_processing_role
}