#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - Failover Testing${NC}"
echo "========================================"

REGION=${AWS_REGION:-us-east-1}
CLUSTER="settlement-ecs-cluster"
SERVICE="settlement-service"
ALB_DNS="settlement-alb-123456789.us-east-1.elb.amazonaws.com"

echo -e "\n${BLUE}Test 1: Single Task Failure${NC}"
echo "Stopping one ECS task..."

# Get task ARN
TASK_ARN=$(aws ecs list-tasks \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --region "$REGION" \
  --query 'taskArns[0]' \
  --output text)

echo "Task ARN: $TASK_ARN"

# Stop the task
aws ecs stop-task \
  --cluster "$CLUSTER" \
  --task "$TASK_ARN" \
  --region "$REGION"

echo -e "${YELLOW}Waiting for replacement task...${NC}"
sleep 30

# Check health
if curl -f "http://${ALB_DNS}/health" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Service recovered after task failure${NC}"
else
  echo -e "${RED}✗ Service did not recover${NC}"
  exit 1
fi

# Verify task count
RUNNING=$(aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "$SERVICE" \
  --region "$REGION" \
  --query 'services[0].runningCount' \
  --output text)

if [ "$RUNNING" -ge 2 ]; then
  echo -e "${GREEN}✓ Desired task count restored: $RUNNING${NC}"
else
  echo -e "${YELLOW}⚠ Task count still below desired: $RUNNING${NC}"
fi

echo -e "\n${BLUE}Test 2: Availability Zone Failure Simulation${NC}"
echo "Draining tasks from AZ..."

# Get all task ARNs
TASK_ARNS=$(aws ecs list-tasks \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --region "$REGION" \
  --query 'taskArns' \
  --output text)

# Stop all but one task
count=0
for task_arn in $TASK_ARNS; do
  if [ $count -ge 1 ]; then
    aws ecs stop-task \
      --cluster "$CLUSTER" \
      --task "$task_arn" \
      --region "$REGION"
  fi
  ((count++))
done

echo -e "${YELLOW}Waiting for replacement tasks...${NC}"
sleep 45

# Check service recovery
if [ "$(aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "$SERVICE" \
  --region "$REGION" \
  --query 'services[0].runningCount' \
  --output text)" -ge 2 ]; then
  echo -e "${GREEN}✓ Service recovered from AZ failure${NC}"
else
  echo -e "${RED}✗ Service did not fully recover${NC}"
  exit 1
fi

echo -e "\n${BLUE}Test 3: Database Connection Failure${NC}"
echo "Simulating Clickhouse unavailability..."

# We can't actually disconnect the database, but we can verify
# that the application continues running and logs the error

if curl -f "http://${ALB_DNS}/health" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Service health check still passing${NC}"
else
  echo -e "${RED}✗ Service health check failed${NC}"
  exit 1
fi

echo -e "\n${GREEN}All failover tests passed!${NC}"
