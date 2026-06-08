terraform {
  required_version = ">= 1.5.0"
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

  # Configure S3 bucket backend with state locking
  backend "s3" {
    bucket         = "propgenie-terraform-state"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "propgenie-terraform-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

module "lambda" {
  source = "./modules/lambda"

  environment                    = var.environment
  lambda_memory                  = var.lambda_memory
  lambda_timeout                 = var.lambda_timeout
  mongodb_uri                    = var.mongodb_uri
  langfuse_secret_key            = var.langfuse_secret_key
  langfuse_public_key            = var.langfuse_public_key
  langfuse_base_url              = var.langfuse_base_url
  reserved_concurrent_executions = var.reserved_concurrent_executions
}

module "frontend" {
  source = "./modules/frontend"

  environment         = var.environment
  agent_function_url  = module.lambda.agent_function_url
  agent_function_name = module.lambda.agent_function_name
  price_class         = var.cloudfront_price_class
  use_custom_domain   = var.use_custom_domain
  custom_domain       = var.custom_domain
  hosted_zone_name    = var.hosted_zone_name

  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }
}

module "monitoring" {
  source = "./modules/monitoring"

  environment         = var.environment
  agent_function_name = module.lambda.agent_function_name
  alarm_email         = var.alarm_email
}



