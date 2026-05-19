variable "environment" {
  type        = string
  description = "The target deployment environment (e.g. dev, prod)"
}

variable "agent_function_url" {
  type        = string
  description = "The URL of the agent Lambda function"
}

variable "agent_function_name" {
  type        = string
  description = "The name of the agent Lambda function"
}

variable "price_class" {
  type        = string
  default     = "PriceClass_100"
  description = "The price class for the CloudFront distribution (e.g., PriceClass_100, PriceClass_200, PriceClass_All)"
}
