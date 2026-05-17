terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Input variables for bootstrap phase
variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "The AWS region to deploy resources in"
}

variable "project_name" {
  type        = string
  default     = "propgenie"
  description = "The name of the project"
}

# Get current caller identity to restrict S3 bucket access to the deploying principal
data "aws_caller_identity" "current" {}

# 1. S3 Bucket for Terraform State
resource "aws_s3_bucket" "state" {
  bucket        = "${var.project_name}-terraform-state"
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

# Enable S3 Versioning
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable Server-side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block Public Access to S3 Bucket
resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 2. S3 Bucket Policy Restricting Access to the Deploying IAM Principal
resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "RestrictToDeployer"
        Effect    = "Allow"
        Principal = {
          AWS = data.aws_caller_identity.current.arn
        }
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.state.arn,
          "${aws_s3_bucket.state.arn}/*"
        ]
      },
      {
        Sid       = "DenyOtherAccess"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.state.arn,
          "${aws_s3_bucket.state.arn}/*"
        ]
        Condition = {
          ArnNotEquals = {
            "aws:PrincipalArn" = data.aws_caller_identity.current.arn
          }
        }
      }
    ]
  })
}

# 3. DynamoDB Table for State Locking
resource "aws_dynamodb_table" "lock" {
  name         = "${var.project_name}-terraform-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Outputs for setup
output "state_bucket_name" {
  value       = aws_s3_bucket.state.id
  description = "The name of the S3 bucket created for Terraform state"
}

output "dynamodb_lock_table_name" {
  value       = aws_dynamodb_table.lock.name
  description = "The name of the DynamoDB table created for state locking"
}

output "deployer_principal_arn" {
  value       = data.aws_caller_identity.current.arn
  description = "The ARN of the deploying IAM principal"
}
