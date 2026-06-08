terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# 1. S3 Bucket for static assets hosting
resource "aws_s3_bucket" "frontend" {
  bucket        = "propgenie-frontend-${var.environment}"
  force_destroy = var.environment == "dev" # Allow easy cleanup in dev
}

# Block public access to the S3 bucket
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning on the S3 bucket
resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Configure lifecycle rule to retain only the last 2 versions (current + 1 noncurrent)
resource "aws_s3_bucket_lifecycle_configuration" "frontend_lifecycle" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    id     = "retain-last-two-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days           = 1
      newer_noncurrent_versions = 1
    }
  }
}


# 2. CloudFront Origin Access Control (OAC) for S3
resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "propgenie-s3-oac-${var.environment}"
  description                       = "OAC for PropGenie Frontend S3 bucket (${var.environment})"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Origin Access Control (OAC) for Lambda Function URL
resource "aws_cloudfront_origin_access_control" "lambda_oac" {
  name                              = "propgenie-lambda-oac-${var.environment}"
  description                       = "OAC for PropGenie Agent Lambda Function URL (${var.environment})"
  origin_access_control_origin_type = "lambda"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# 3. Custom Origin Request Policy to forward CloudFront-Viewer-Address to the Lambda function
resource "aws_cloudfront_origin_request_policy" "lambda_policy" {
  name    = "propgenie-lambda-request-policy-${var.environment}"
  comment = "Forward client IP, session ID, and standard API headers to Lambda (${var.environment})"

  cookies_config {
    cookie_behavior = "all"
  }

  headers_config {
    header_behavior = "whitelist"
    headers {
      items = [
        "CloudFront-Viewer-Address",
        "X-Session-ID",
        "Content-Type",
        "Accept"
      ]
    }
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

# 4. CloudFront Distribution
resource "aws_cloudfront_distribution" "distribution" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = var.price_class

  # S3 static assets origin
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id
  }

  # Lambda API origin (stripping https:// and trailing / from Lambda Function URL)
  origin {
    domain_name              = replace(replace(var.agent_function_url, "https://", ""), "/", "")
    origin_id                = "lambda-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.lambda_oac.id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default cache behavior for S3 static files (CachingOptimized)
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Managed CachingOptimized Policy ID
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  # Ordered cache behavior for /api/* requests (CachingDisabled + Custom Origin Request Policy)
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "lambda-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # Managed CachingDisabled Policy ID
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"

    # Custom request policy to forward headers/query params/cookies to Lambda
    origin_request_policy_id = aws_cloudfront_origin_request_policy.lambda_policy.id
  }

  # Custom error responses for SPA routing (403 and 404 redirected to index.html)
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  # Required default settings
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# 5. S3 Bucket Policy allowing CloudFront OAC read access
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowCloudFrontServicePrincipal"
        Effect   = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.distribution.arn
          }
        }
      }
    ]
  })
}

# 6. Grant CloudFront OAC permission to invoke the Lambda Function URL
resource "aws_lambda_permission" "allow_cloudfront" {
  statement_id           = "AllowCloudFrontInvoke"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = var.agent_function_name
  principal              = "cloudfront.amazonaws.com"
  source_arn             = aws_cloudfront_distribution.distribution.arn
  function_url_auth_type = "AWS_IAM"
}

# Grant CloudFront OAC permission to invoke the Lambda Function directly (sometimes required by OAC)
resource "aws_lambda_permission" "allow_cloudfront_invoke" {
  statement_id  = "AllowCloudFrontInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = var.agent_function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = aws_cloudfront_distribution.distribution.arn
}
