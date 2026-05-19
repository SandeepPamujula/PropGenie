output "agent_function_url" {
  value       = aws_lambda_function_url.agent_url.function_url
  description = "The URL endpoint for the agent Lambda function"
}

output "agent_function_arn" {
  value       = aws_lambda_function.agent.arn
  description = "The ARN of the agent Lambda function"
}

output "agent_function_name" {
  value       = aws_lambda_function.agent.function_name
  description = "The name of the agent Lambda function"
}
