variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "stage" {
  description = "Stage name"
  type        = string
  default     = "localstack"
}
