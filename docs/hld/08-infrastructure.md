# 8. Infrastructure (Terraform)

## 8.1 Resource Inventory

| Resource | Terraform Resource Type | Purpose |
|----------|------------------------|---------|
| S3 Bucket (frontend) | `aws_s3_bucket` | Static Next.js assets |
| S3 Bucket Policy | `aws_s3_bucket_policy` | CloudFront OAC access |
| CloudFront Distribution | `aws_cloudfront_distribution` | CDN + `/api/*` routing to Lambda Function URL + CloudFront-Viewer-Address injection |
| CloudFront OAC | `aws_cloudfront_origin_access_control` | Secure S3 and Lambda Function URL origin access |
| Lambda (Agent) | `aws_lambda_function` | PropGenie LangGraph agent + inline rate limiting |
| Lambda Function URL | `aws_lambda_function_url` | SSE streaming endpoint (AWS_IAM auth) |
| Lambda IAM Role | `aws_iam_role` + `aws_iam_policy` | Least-privilege: Bedrock invoke, CloudWatch logs |
| Lambda Resource Policy | `aws_lambda_permission` | Allow CloudFront to invoke Function URL |
| CloudWatch Log Groups | `aws_cloudwatch_log_group` | Lambda log retention |
| CloudWatch Alarms | `aws_cloudwatch_metric_alarm` | Error rate, cold starts |
| S3 Backend Bucket | `aws_s3_bucket` | Terraform state storage |
| DynamoDB Lock Table | `aws_dynamodb_table` | Terraform state locking |

> **Note:** Secrets (MongoDB URI, Langfuse keys) are injected as Lambda environment variables via Terraform variables sourced from GitHub Actions secrets. No SSM Parameter Store for v1.

## 8.2 Terraform Structure

```
infra/
├── main.tf                  # Provider config, backend
├── variables.tf             # Input variables
├── outputs.tf               # Stack outputs
├── environments/
│   ├── dev.tfvars           # Dev variable values
│   └── prod.tfvars          # Prod variable values
├── modules/
│   ├── frontend/            # S3 + CloudFront
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── lambda/              # Agent Lambda + Function URL
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── monitoring/          # CloudWatch + alarms
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
```

## 8.3 Lambda IAM Permissions (Least-Privilege)

### PropGenie Agent Lambda
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/meta.llama3-1-70b-instruct-*",
    "arn:aws:logs:*:*:log-group:/aws/lambda/propgenie-agent-*"
  ]
}
```

> **Note:** MongoDB Atlas and Langfuse Cloud are accessed over the public internet via connection strings/API keys — no AWS IAM permissions needed.

## 8.4 Workspace Strategy

| Attribute | Dev | Prod |
|-----------|-----|------|
| Workspace | `dev` | `prod` |
| Lambda memory | 512 MB | 1024 MB |
| Lambda timeout | 60s | 60s |
| CloudWatch log retention | 7 days | 30 days |
| CloudFront price class | PriceClass_200 | PriceClass_All |
