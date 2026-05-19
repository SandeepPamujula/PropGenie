# Placeholder for primary infrastructure outputs (e.g. S3 website endpoint, Lambda function URL etc.)
# These will be populated in subsequent milestones.

output "environment" {
  value       = var.environment
  description = "The target deployment environment"
}

output "project_name" {
  value       = var.project_name
  description = "The name of the project"
}

output "aws_region" {
  value       = var.aws_region
  description = "The AWS region"
}

output "agent_function_url" {
  value       = module.lambda.agent_function_url
  description = "The URL endpoint for the agent Lambda function"
}

output "agent_function_arn" {
  value       = module.lambda.agent_function_arn
  description = "The ARN of the agent Lambda function"
}

output "agent_function_name" {
  value       = module.lambda.agent_function_name
  description = "The name of the agent Lambda function"
}

