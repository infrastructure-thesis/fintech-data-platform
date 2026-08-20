#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

CLUSTER="settlement-ecs-cluster"
SERVICE="settlement-service"
REGION="us-east-1"
MONITORING_WINDOW=300  # 5 minutes per stage

echo -e "${BLUE}Settlement Pipeline - Canary Deployment${NC}"
echo "=========================================="
echo "Cluster: $CLUSTER"
echo "Service: $SERVICE"
echo "Region: $REGION"

# Stage 1: Canary 5%
echo -e "\n${YELLOW}Stage 1: Canary Deployment (5% traffic)${NC}"
echo "Scaling to 1 task (5% of 20)..."

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --desired-count 1 \
  --region "$REGION"

echo "Monitoring for $MONITORING_WINDOW seconds..."
sleep "$MONITORING_WINDOW"

ERROR_RATE=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --start-time "$(date -u -d "$((MONITORING_WINDOW/60)) minutes ago" +%Y-%m-%dT%H:%M:%S)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
  --period 60 \
  --statistics Sum \
  --region "$REGION" \
  --query 'Datapoints[0].Sum' \
  --output text)

if [ "$ERROR_RATE" == "None" ] || [ "$ERROR_RATE" == "0" ]; then
  echo -e "${GREEN}✓ Canary stage 1 healthy (error rate: 0%)${NC}"
else
  echo -e "${RED}✗ Canary stage 1 failed (errors detected)${NC}"
  echo "Rolling back..."
  aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --desired-count 3 --region "$REGION"
  exit 1
fi

# Stage 2: Canary 25%
echo -e "\n${YELLOW}Stage 2: Canary Deployment (25% traffic)${NC}"
echo "Scaling to 5 tasks (25% of 20)..."

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --desired-count 5 \
  --region "$REGION"

echo "Monitoring for $MONITORING_WINDOW seconds..."
sleep "$MONITORING_WINDOW"

if [ "$ERROR_RATE" == "None" ] || [ "$ERROR_RATE" == "0" ]; then
  echo -e "${GREEN}✓ Canary stage 2 healthy${NC}"
else
  echo -e "${RED}✗ Canary stage 2 failed${NC}"
  echo "Rolling back..."
  aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --desired-count 3 --region "$REGION"
  exit 1
fi

# Stage 3: Full Deployment
echo -e "\n${YELLOW}Stage 3: Full Deployment (100% traffic)${NC}"
echo "Scaling to 20 tasks (100%)..."

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --desired-count 20 \
  --region "$REGION"

echo "Monitoring for $((MONITORING_WINDOW * 2)) seconds..."
sleep "$((MONITORING_WINDOW * 2))"

echo -e "\n${GREEN}✅ Deployment successful!${NC}"
echo "All canary stages passed. Service is running at full capacity."
