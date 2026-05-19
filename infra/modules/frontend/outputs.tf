output "cloudfront_domain" {
  value       = aws_cloudfront_distribution.distribution.domain_name
  description = "The domain name of the CloudFront distribution"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.frontend.id
  description = "The name of the S3 bucket hosting static assets"
}

output "distribution_id" {
  value       = aws_cloudfront_distribution.distribution.id
  description = "The ID of the CloudFront distribution"
}
