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
