#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME="settlement-ecs-cluster"
SERVICE_NAME="settlement-service"

echo -e "${BLUE}Settlement Pipeline - Deployment Validation${NC}"
echo "==========================================="

# 1. Check ECS service status
echo -e "\n${BLUE}1. Checking ECS service status...${NC}"
RUNNING=$(aws ecs describe-services \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME" \
  --region "$REGION" \
  --query 'services[0].runningCount' \
  --output text)

if [ "$RUNNING" -ge 2 ]; then
  echo -e "${GREEN}✓ Service running with $RUNNING tasks${NC}"
else
  echo -e "${RED}✗ Service not healthy: only $RUNNING tasks running${NC}"
  exit 1
fi

# 2. Check ALB health
echo -e "\n${BLUE}2. Checking ALB target health...${NC}"
HEALTHY=$(aws elbv2 describe-target-health \
  --target-group-arn "arn:aws:elasticloadbalancing:${REGION}:$(aws sts get-caller-identity --query Account --output text):targetgroup/settlement-tg/*" \
  --query 'TargethealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
  --services "$SERVICE_NAME" \
  --output text 2>/dev/null || echo "0")

if [ "$HEALTHY" -ge 2 ]; then
  echo -e "${GREEN}✓ $HEALTHY healthy targets${NC}"
else
  echo -e "${YELLOW}⚠ Only $HEALTHY healthy targets (still stabilizing?)${NC}"
fi

# 3. Get ALB DNS
echo -e "\n${BLUE}3. Checking API endpoint...${NC}"
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names settlement-alb \
  --region "$REGION" \
  --query 'LoadBalancers[0].DNSName' \
  --output text 2>/dev/null || echo "unknown")

if [ "$ALB_DNS" != "unknown" ]; then
  echo -e "${GREEN}✓ ALB DNS: $ALB_DNS${NC}"

  # Test health endpoint
  if curl -f -s "http://${ALB_DNS}/health" > /dev/null; then
    echo -e "${GREEN}✓ Health endpoint responding${NC}"
  else
    echo -e "${YELLOW}⚠ Health endpoint not yet responding${NC}"
  fi
else
    echo -e "${RED}✗ Could not find ALB${NC}"
fi

# 4. Check logs
echo -e "\n${BLUE}4. Checking CloudWatch logs...${NC}"
RECENT_LOGS=$(aws logs tail /ecs/settlement-pipeline \
  --since 5m \
  --max-items 5 \
  --region "$REGION" 2>/dev/null || echo "No logs yet")

echo "$RECENT_LOGS" | head -5

# 5. Check auto-scaling
echo -e "\n${BLUE}5. Checking auto-scaling configuration...${NC}"
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --region "$REGION" \
  --resource-ids "service/${CLUSTER_NAME}/${SERVICE_NAME}" \
  --query 'ScalableTargets[0].[MinCapacity,MaxCapacity]' \
  --output text | xargs echo "Scaling range:"

echo -e "\n${GREEN}Validation complete!${NC}"
