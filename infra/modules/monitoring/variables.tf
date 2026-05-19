variable "environment" {
  type        = string
  description = "The target deployment environment (e.g. dev, prod)"
}

variable "agent_function_name" {
  type        = string
  description = "The name of the agent Lambda function"
}

variable "alarm_email" {
  type        = string
  description = "The email address to receive CloudWatch alarms"
}
