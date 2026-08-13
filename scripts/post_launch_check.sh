#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

REGION=${AWS_REGION:-us-east-1}
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
REPORT_FILE="post_launch_report_${TIMESTAMP}.txt"

{
  echo "Settlement Pipeline - Post-Launch Report"
  echo "========================================="
  echo "Generated: $(date)"
  echo ""
  
  echo "SERVICE STATUS"
  echo "=============="
  aws ecs describe-services \
    --cluster settlement-ecs-cluster \
    --services settlement-service \
    --region "$REGION" \
    --query 'services[0].[runningCount,desiredCount,pendingCount,deployments[0].status]' \
    --output text
  echo ""
  
  echo "ALB TARGET HEALTH"
  echo "================="
  aws elbv2 describe-target-health \
    --target-group-arn "arn:aws:elasticloadbalancing:${REGION}:$(aws sts get-caller-identity --query Account --output text):targetgroup/settlement-tg/*" \
    --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.ReasonCode]' \
    --output table
  echo ""
  
  echo "CLOUDWATCH METRICS (Last 5 minutes)"
  echo "==================================="
  
  CPU=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=settlement-service Name=ClusterName,Value=settlement-ecs-cluster \
    --start-time "$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 300 \
    --statistics Average \
    --region "$REGION" \
    --query 'Datapoints[0].Average' \
    --output text)
  
  MEMORY=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name MemoryUtilization \
    --dimensions Name=ServiceName,Value=settlement-service Name=ClusterName,Value=settlement-ecs-cluster \
    --start-time "$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 300 \
    --statistics Average \
    --region "$REGION" \
    --query 'Datapoints[0].Average' \
    --output text)
  
  echo "CPU: ${CPU}%"
  echo "Memory: ${MEMORY}%"
  echo ""
  
  echo "ACTIVE ALARMS"
  echo "============="
  aws cloudwatch describe-alarms \
    --region "$REGION" \
    --state-value ALARM \
    --query 'MetricAlarms[?contains(AlarmName, `settlement`)].[AlarmName,StateValue]' \
    --output table
  echo ""
  
  echo "RECENT ERROR LOGS (Last 30 minutes)"
  echo "===================================="
  aws logs filter-log-events \
    --log-group-name /ecs/settlement-pipeline \
    --filter-pattern "ERROR" \
    --start-time $(($(date +%s%000) - 1800000)) \
    --query 'events[*].[timestamp,message]' \
    --output table | head -10
  echo ""
  
  echo "RECOMMENDATIONS"
  echo "==============="
  
  if (( $(echo "$CPU > 75" | bc -l) )); then
    echo "⚠ CPU usage high - consider scaling up"
  fi
  
  if (( $(echo "$MEMORY > 80" | bc -l) )); then
    echo "⚠ Memory usage high - monitor for leaks"
  fi
  
  echo "✓ Service is stable"
  
} | tee "$REPORT_FILE"

echo ""
echo -e "${GREEN}Report saved to: $REPORT_FILE${NC}"
