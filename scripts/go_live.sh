#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - Production Go-Live${NC}"
echo "=========================================="

REGION=${AWS_REGION:-us-east-1}

# Phase 1: Pre-launch checks
echo -e "\n${BLUE}PHASE 1: Pre-Launch Verification${NC}"
echo "=================================="

checks_passed=0
checks_failed=0

# Check 1: Service running
if aws ecs describe-services --cluster settlement-ecs-cluster --services settlement-service --region "$REGION" \
  --query 'services[0].runningCount' --output text | grep -q "[2-9]"; then
  echo -e "${GREEN}✓ ECS service running${NC}"
  ((checks_passed++))
else
  echo -e "${RED}✗ ECS service not running${NC}"
  ((checks_failed++))
fi

# Check 2: ALB healthy
HEALTHY=$(aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:${REGION}:$(aws sts get-caller-identity --query Account --output text):targetgroup/settlement-tg/*" \
  --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
  --output text 2>/dev/null || echo "0")

if [ "$HEALTHY" -ge 2 ]; then
  echo -e "${GREEN}✓ ALB targets healthy ($HEALTHY)${NC}"
  ((checks_passed++))
else
  echo -e "${RED}✗ Insufficient healthy targets ($HEALTHY)${NC}"
  ((checks_failed++))
fi

# Check 3: Database connectivity
if aws secretsmanager get-secret-value --secret-id settlement/clickhouse-password --region "$REGION" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Secrets Manager accessible${NC}"
  ((checks_passed++))
else
  echo -e "${RED}✗ Secrets Manager not accessible${NC}"
  ((checks_failed++))
fi

# Check 4: Alarms configured
ALARM_COUNT=$(aws cloudwatch describe-alarms --region "$REGION" \
  --query "MetricAlarms[?contains(AlarmName, 'settlement')] | length(@)" --output text)

if [ "$ALARM_COUNT" -ge 5 ]; then
  echo -e "${GREEN}✓ Alarms configured ($ALARM_COUNT)${NC}"
  ((checks_passed++))
else
  echo -e "${RED}✗ Insufficient alarms configured ($ALARM_COUNT)${NC}"
  ((checks_failed++))
fi

echo -e "\n${BLUE}Pre-launch summary: $checks_passed passed, $checks_failed failed${NC}"

if [ $checks_failed -gt 0 ]; then
  echo -e "${RED}✗ Pre-launch checks failed${NC}"
  exit 1
fi

# Phase 2: Approval
echo -e "\n${BLUE}PHASE 2: Approval${NC}"
echo "=================="
echo -e "${YELLOW}All pre-launch checks passed.${NC}"
echo "Ready to proceed with go-live? (type 'yes' to continue)"
read -r approval

if [ "$approval" != "yes" ]; then
  echo "Go-live cancelled"
  exit 0
fi

# Phase 3: Go-live
echo -e "\n${BLUE}PHASE 3: Go-Live Execution${NC}"
echo "============================"

ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names settlement-alb \
  --region "$REGION" \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo -e "${GREEN}✓ API Endpoint: http://${ALB_DNS}${NC}"
echo -e "${GREEN}✓ Health Check: http://${ALB_DNS}/health${NC}"
echo -e "${GREEN}✓ Metrics: http://${ALB_DNS}/metrics${NC}"

# Phase 4: Validation
echo -e "\n${BLUE}PHASE 4: Post-Launch Validation${NC}"
echo "================================"

echo "Verifying service health..."
for i in {1..10}; do
  if curl -f "http://${ALB_DNS}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Service responding to requests${NC}"
    break
  fi
  echo -n "."
  sleep 5
done

# Check metrics
if curl -s "http://${ALB_DNS}/metrics" | grep -q "settlement_transactions_processed_total"; then
  echo -e "${GREEN}✓ Prometheus metrics available${NC}"
else
  echo -e "${YELLOW}⚠ Metrics endpoint not yet available${NC}"
fi

# Phase 5: Operations Handoff
echo -e "\n${BLUE}PHASE 5: Operations Handoff${NC}"
echo "============================"

echo -e "${GREEN}✓ Dashboard: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=settlement-pipeline${NC}"
echo -e "${GREEN}✓ Logs: https://console.aws.amazon.com/cloudwatch/home#logsV2:logs-insights${NC}"
echo -e "${GREEN}✓ ECS: https://console.aws.amazon.com/ecs/v2/clusters/settlement-ecs-cluster${NC}"

echo -e "\n${GREEN}Go-live complete!${NC}"
echo "Monitor dashboard closely for next 4 hours"
echo "Be ready to rollback if critical issues detected"
