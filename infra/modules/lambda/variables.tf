variable "environment" {
  type        = string
  description = "The target deployment environment (e.g. dev, prod)"
}

variable "lambda_memory" {
  type        = number
  description = "Amount of memory in MB to allocate to the Lambda function"
}

variable "lambda_timeout" {
  type        = number
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
  description = "Langfuse Base/Host URL"
}

variable "reserved_concurrent_executions" {
  type        = number
  description = "Amount of reserved concurrent executions for this Lambda function"
}

variable "cloudfront_distribution_arn" {
  type        = string
  default     = null
  description = "Optional ARN of the CloudFront distribution allowed to invoke the Lambda Function URL"
}
