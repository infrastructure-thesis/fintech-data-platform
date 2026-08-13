#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

REGION=${AWS_REGION:-us-east-1}
REPORT_FILE="performance_analysis_$(date +%Y%m%d_%H%M%S).txt"

{
  echo "Settlement Pipeline - Performance Analysis Report"
  echo "=================================================="
  echo "Generated: $(date)"
  echo ""

  echo "1. LATENCY ANALYSIS (Last 24 hours)"
  echo "===================================="
  
  aws cloudwatch get-metric-statistics \
    --namespace settlement-pipeline \
    --metric-name pipeline_latency_seconds \
    --dimensions Name=stage,Value=consumer \
    --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 3600 \
    --statistics Average,Maximum \
    --region "$REGION" \
    --output table
  
  echo ""
  echo "2. THROUGHPUT ANALYSIS"
  echo "======================"
  
  aws cloudwatch get-metric-statistics \
    --namespace settlement-pipeline \
    --metric-name transactions_processed_total \
    --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 3600 \
    --statistics Sum \
    --region "$REGION" \
    --output table
  
  echo ""
  echo "3. RESOURCE UTILIZATION"
  echo "======================="
  
  CPU=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=settlement-service Name=ClusterName,Value=settlement-ecs-cluster \
    --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 3600 \
    --statistics Average,Maximum \
    --region "$REGION" \
    --query 'Datapoints | sort_by(@, &Timestamp)[-1]' \
    --output text)
  
  echo "CPU (Last hour): $CPU"
  
  MEMORY=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name MemoryUtilization \
    --dimensions Name=ServiceName,Value=settlement-service Name=ClusterName,Value=settlement-ecs-cluster \
    --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 3600 \
    --statistics Average,Maximum \
    --region "$REGION" \
    --query 'Datapoints | sort_by(@, &Timestamp)[-1]' \
    --output text)
  
  echo "Memory (Last hour): $MEMORY"
  
  echo ""
  echo "4. SCALING EVENTS"
  echo "================="
  
  aws autoscaling describe-scaling-activities \
    --auto-scaling-group-name settlement-ecs-scaling-group \
    --max-records 10 \
    --region "$REGION" \
    --query 'Activities[].[StartTime,Description]' \
    --output table 2>/dev/null || echo "No scaling group events"
  
  echo ""
  echo "5. ERROR TRENDS"
  echo "==============="
  
  aws cloudwatch get-metric-statistics \
    --namespace settlement-pipeline \
    --metric-name transactions_failed_total \
    --start-time "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 3600 \
    --statistics Sum \
    --region "$REGION" \
    --output table
  
  echo ""
  echo "6. RECOMMENDATIONS"
  echo "=================="
  echo "✓ Monitor Clickhouse write latency"
  echo "✓ Review Kafka consumer lag"
  echo "✓ Analyze error patterns from logs"
  echo "✓ Consider batch size optimization"
  echo "✓ Plan capacity for next 30 days"
  
} | tee "$REPORT_FILE"

echo ""
echo -e "${GREEN}Report saved: $REPORT_FILE${NC}"
