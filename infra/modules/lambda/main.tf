terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

# Create a dummy zip file for bootstrapping the Lambda function
data "archive_file" "dummy" {
  type        = "zip"
  output_path = "${path.module}/dummy_lambda.zip"

  source {
    content  = "def lambda_handler(event, context):\n    return {'statusCode': 200, 'body': 'Bootstrap'}"
    filename = "handler.py"
  }
}

# IAM Execution Role for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "propgenie-agent-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Least-Privilege IAM Policy for Lambda Execution
resource "aws_iam_policy" "lambda_policy" {
  name        = "propgenie-agent-policy-${var.environment}"
  description = "Least-privilege policy for PropGenie Agent Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/meta.llama3-1-70b-instruct-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:*:*:log-group:/aws/lambda/propgenie-agent-${var.environment}:*"
        ]
      }
    ]
  })
}

# Attach IAM Policy to Role
resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# PropGenie Agent Lambda Function
resource "aws_lambda_function" "agent" {
  function_name                  = "propgenie-agent-${var.environment}"
  description                    = "PropGenie Agent LangGraph Backend (${var.environment})"
  role                           = aws_iam_role.lambda_exec.arn
  handler                        = "handler.lambda_handler"
  runtime                        = "python3.12"
  memory_size                    = var.lambda_memory
  timeout                        = var.lambda_timeout
  reserved_concurrent_executions = var.reserved_concurrent_executions

  filename         = data.archive_file.dummy.output_path
  source_code_hash = data.archive_file.dummy.output_base64sha256

  environment {
    variables = {
      MONGODB_URI         = var.mongodb_uri
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_BASE_URL   = var.langfuse_base_url
      LANGFUSE_HOST       = var.langfuse_base_url
      ENVIRONMENT         = var.environment
    }
  }

  lifecycle {
    # Ignore changes to code zip updated in CI/CD deployment
    ignore_changes = [
      filename,
      source_code_hash
    ]
  }
}

# Configure Lambda Function URL with AWS_IAM auth type and RESPONSE_STREAM mode
resource "aws_lambda_function_url" "agent_url" {
  function_name      = aws_lambda_function.agent.function_name
  authorization_type = "AWS_IAM"
  invoke_mode        = "RESPONSE_STREAM"
}

