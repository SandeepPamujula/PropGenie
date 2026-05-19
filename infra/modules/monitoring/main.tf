terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# 1. Log Group for Agent Lambda (retention: dev 7 days, prod 30 days)
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.agent_function_name}"
  retention_in_days = var.environment == "prod" ? 30 : 7
}

# 2. Metric Filters
# Lambda error count (filter pattern: ERROR)
resource "aws_cloudwatch_log_metric_filter" "lambda_errors" {
  name           = "lambda-errors-${var.environment}"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.lambda_log_group.name

  metric_transformation {
    name      = "ErrorCount"
    namespace = "PropGenie/Lambda"
    value     = "1"
  }
}

# Rate limit breach count (filter pattern: RATE_LIMIT_EXCEEDED)
resource "aws_cloudwatch_log_metric_filter" "rate_limit_breaches" {
  name           = "rate-limit-breaches-${var.environment}"
  pattern        = "RATE_LIMIT_EXCEEDED"
  log_group_name = aws_cloudwatch_log_group.lambda_log_group.name

  metric_transformation {
    name      = "RateLimitBreachCount"
    namespace = "PropGenie/Lambda"
    value     = "1"
  }
}

# Cold start count (filter pattern: Init Duration)
resource "aws_cloudwatch_log_metric_filter" "cold_starts" {
  name           = "cold-starts-${var.environment}"
  pattern        = "\"Init Duration\""
  log_group_name = aws_cloudwatch_log_group.lambda_log_group.name

  metric_transformation {
    name      = "ColdStartCount"
    namespace = "PropGenie/Lambda"
    value     = "1"
  }
}

# 3. SNS Topic for Alarm Notifications
resource "aws_sns_topic" "alerts" {
  name = "propgenie-alerts-${var.environment}"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# 4. CloudWatch Alarms
# Lambda error rate > 1%
resource "aws_cloudwatch_metric_alarm" "lambda_error_rate" {
  alarm_name          = "propgenie-lambda-error-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 1 # 1%
  alarm_description   = "Alarm when Lambda error rate exceeds 1%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  # Metric query math: error rate = (errors / invocations) * 100
  metric_query {
    id          = "error_rate"
    expression  = "errors / invocations * 100"
    label       = "Error Rate (%)"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 60
      stat        = "Sum"
      dimensions = {
        FunctionName = var.agent_function_name
      }
    }
  }

  metric_query {
    id = "invocations"
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Lambda"
      period      = 60
      stat        = "Sum"
      dimensions = {
        FunctionName = var.agent_function_name
      }
    }
  }
}

# Cold starts > 10 per minute
resource "aws_cloudwatch_metric_alarm" "cold_starts" {
  alarm_name          = "propgenie-lambda-cold-starts-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ColdStartCount"
  namespace           = "PropGenie/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alarm when Lambda cold starts exceed 10 per minute"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}
