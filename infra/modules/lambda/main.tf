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

# 1. Prepare backend dist directory using python script (runs cross-platform)
resource "null_resource" "prepare_backend_dist" {
  triggers = {
    requirements = filesha256("${path.root}/../backend/requirements.txt")
    always_run   = timestamp()
  }

  provisioner "local-exec" {
    working_dir = "${path.root}/.."
    command     = "python backend/scripts/prepare_dist.py"
  }
}

# 2. Archive the prepared build directory containing code and dependencies (deferred to apply phase)
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_backend.zip"
  source_dir  = "${path.root}/../backend/dist"

  depends_on = [null_resource.prepare_backend_dist]
}

# 3. Upload zip to S3 (since the package exceeds AWS Lambda direct upload size limits)
resource "aws_s3_object" "lambda_zip_upload" {
  bucket     = "propgenie-terraform-state"
  key        = "lambda_packages/lambda_backend_${var.environment}.zip"
  source     = data.archive_file.lambda_zip.output_path
  etag       = data.archive_file.lambda_zip.output_md5
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
          "arn:aws:bedrock:*::foundation-model/meta.llama3-1-70b-instruct-*",
          "arn:aws:bedrock:*::foundation-model/us.meta.llama3-1-70b-instruct-*",
          "arn:aws:bedrock:*:*:inference-profile/us.meta.llama3-1-70b-instruct-*"
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

  s3_bucket        = aws_s3_object.lambda_zip_upload.bucket
  s3_key           = aws_s3_object.lambda_zip_upload.key
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      MONGODB_URI         = var.mongodb_uri
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_BASE_URL   = var.langfuse_base_url
      LANGFUSE_HOST       = var.langfuse_base_url
      ENVIRONMENT         = var.environment
      BEDROCK_REGION      = "us-east-1"
      BEDROCK_MODEL_ID    = "us.meta.llama3-1-70b-instruct-v1:0"
    }
  }

  lifecycle {
    # Allow Terraform to update the Lambda when the code zip changes
    ignore_changes = []
  }
}

# Configure Lambda Function URL with AWS_IAM auth type and BUFFERED mode
resource "aws_lambda_function_url" "agent_url" {
  function_name      = aws_lambda_function.agent.function_name
  authorization_type = "AWS_IAM"
  invoke_mode        = "BUFFERED"
}

