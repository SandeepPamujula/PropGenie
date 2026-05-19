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

variable "lambda_memory" {
  type        = number
  description = "Amount of memory in MB to allocate to the Lambda function"
}

variable "lambda_timeout" {
  type        = number
  default     = 60
  description = "Maximum time in seconds the Lambda function can run"
}

variable "mongodb_uri" {
  type        = string
  sensitive   = true
  description = "MongoDB connection string"
}

variable "langfuse_secret_key" {
  type        = string
  sensitive   = true
  description = "Langfuse Secret Key"
}

variable "langfuse_public_key" {
  type        = string
  sensitive   = true
  description = "Langfuse Public Key"
}

variable "langfuse_base_url" {
  type        = string
  default     = "https://cloud.langfuse.com"
  description = "Langfuse Base/Host URL"
}

variable "reserved_concurrent_executions" {
  type        = number
  description = "Amount of reserved concurrent executions for this Lambda function"
}

variable "cloudfront_price_class" {
  type        = string
  default     = "PriceClass_100"
  description = "The price class for the CloudFront distribution (e.g., PriceClass_100, PriceClass_200, PriceClass_All)"
}

variable "alarm_email" {
  type        = string
  description = "The email address to receive CloudWatch alarms"
}



