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
variable "earthdata_username" {
    type = string
    default = ""
}

variable "earthdata_password" {
    type = string
    default = ""
}
