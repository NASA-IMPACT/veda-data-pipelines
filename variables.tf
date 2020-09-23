variable "batch_ec2_volume_size" {
    type = number
    default = 30
}

variable "subnet_ids" {
    type = list
    default = []
}

variable "lambda_processing_role" {
    type = string
    default = ""
}

variable "batch_image_id" {
    type = string
    default = ""
}

variable "deployment_prefix" {
    type = string
    default = "cloud-optimized-dp"
}
