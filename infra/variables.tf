variable "environment" {
  type        = string
  description = "The target deployment environment (e.g. dev, prod)"
}

variable "project_name" {
  type        = string
  default     = "propgenie"
  description = "The name of the project"
}

variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "The AWS region to deploy resources in"
}
