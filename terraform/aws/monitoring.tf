# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "settlement-pipeline"

  dashboard_body = jsonencode({
    widgets = [
      # Row 1: Overview
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "settlement-service", "ClusterName", "settlement-ecs-cluster"],
            [".", "MemoryUtilization", ".", ".", ".", ".", ],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/settlement-alb/*"],
            [".", "RequestCount", ".", "."]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Service Health"
        }
      },
      # Row 2: API Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["settlement-pipeline", "transaction_processed_total", { stat = "Sum" }],
            [".", "transaction_failed_total", { stat = "Sum" }],
            [".", "pipeline_latency_seconds", { stat = "Average" }],
            [".", "active_batches", { stat = "Average" }]
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Pipeline Metrics"
        }
      },
      # Row 3: Error Tracking
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", "app/settlement-alb/*"],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "TargetConnectionErrorCount", ".", "."]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Error Rates"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      # Row 4: Logs
      {
        type = "log"
        properties = {
          query  = "fields @timestamp, @message | filter @message like /ERROR/ | stats count() by @message"
          region = var.aws_region
          title  = "Recent Errors"
        }
      }
    ]
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "settlement_alerts" {
  name = "settlement-alerts"

  tags = {
    Name = "settlement-alerts"
  }
}

resource "aws_sns_topic_subscription" "settlement_alerts_email" {
  topic_arn = aws_sns_topic.settlement_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarms

# 1. ECS CPU Utilization
resource "aws_cloudwatch_metric_alarm" "ecs_cpu" {
  alarm_name          = "settlement-ecs-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Alert when ECS CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.settlement_alerts.arn]

  dimensions = {
    ServiceName = "settlement-service"
    ClusterName = "settlement-ecs-cluster"
  }

  tags = {
    Name = "settlement-cpu-alarm"
  }
}

# 2. ECS Memory Utilization
resource "aws_cloudwatch_metric_alarm" "ecs_memory" {
  alarm_name          = "settlement-ecs-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Alert when ECS Memory exceeds 85%"
  alarm_actions       = [aws_sns_topic.settlement_alerts.arn]

  dimensions = {
    ServiceName = "settlement-service"
    ClusterName = "settlement-ecs-cluster"
  }

  tags = {
    Name = "settlement-memory-alarm"
  }
}

# 3. ALB Target Health
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_targets" {
  alarm_name          = "settlement-unhealthy-targets"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UnhealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when any target becomes unhealthy"
  alarm_actions       = [aws_sns_topic.settlement_alerts.arn]

  dimensions = {
    TargetGroup  = "targetgroup/settlement-tg/*"
    LoadBalancer = "app/settlement-alb/*"
  }

  tags = {
    Name = "settlement-target-health-alarm"
  }
}

# 4. ALB Response Time
resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  alarm_name          = "settlement-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Average"
  threshold           = 0.5 # 500ms
  alarm_description   = "Alert when response time exceeds 500ms"
  alarm_actions       = [aws_sns_topic.settlement_alerts.arn]

  dimensions = {
    LoadBalancer = "app/settlement-alb/*"
  }

  tags = {
    Name = "settlement-response-time-alarm"
  }
}

# 5. HTTP 5xx Errors
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "settlement-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5xx_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when 5xx errors exceed 10 in 5 minutes"
  alarm_actions       = [aws_sns_topic.settlement_alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = "app/settlement-alb/*"
  }

  tags = {
    Name = "settlement-5xx-alarm"
  }
}

# 6. CloudWatch Log Group Errors
resource "aws_cloudwatch_log_group" "errors" {
  name              = "/ecs/settlement-pipeline-errors"
  retention_in_days = 30

  tags = {
    Name = "settlement-errors-logs"
  }
}

resource "aws_cloudwatch_metric_alarm" "log_errors" {
  alarm_name          = "settlement-log-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 5
  alarm_description   = "Alert when ERRORS logs exceed 5 in 5 minutes"
  alarm_actions       = [aws_sns_topic.settlement_alerts.arn]
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_count"
    expression  = "SEARCH(' {$.level = \"ERROR\" || $.level = \"CRITICAL\") } | stats count()', 'Count', 300)"
    label       = "Error Count"
    return_data = true
  }

  tags = {
    Name = "settlement-log-errors-alarm"
  }
}

# Outputs
output "sns_topic_arn" {
  description = "ARN of SNS topic for alerts"
  value       = aws_sns_topic.settlement_alerts.arn
}

output "dashboard_url" {
  description = "URL to CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=settlement-pipeline"
}
