#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - Load Testing${NC}"
echo "===================================="

# Configuration
ALB_DNS={1:-settlement-alb-123456789.us-east-1.elb.amazonaws.com}
DURATION=${2:-300} # 5 minutes
CONCURRENCY=${3:-10}
REGION=${AWS_REGION:-us-east-1}

echo -e "\n${BLUE}Load Test Configuration:${NC}"
echo "Target: http://${ALB_DNS}"
echo "Duration: {DURATION}s"
echo "Concurrency: ${CONCURRENCY}"

# Pre-test health check
echo -e "\n${BLUE}Pre-test health check...${NC}"
if ! curl -f "http://${ALB_DNS}/health" > /dev/null 2>&1; then
  echo -e "${RED}✗ Service health check failed${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Service is healthy${NC}"

# Start baseline metrics
echo -e "\n${BLUE}Recording baseline metrics...${NC}"
BASELINE_CPU=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,value=settlement-service Name=ClusterName,Value=settlement-ecs-cluster \
  --start-time "$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
  --period 300 \
  --statistics Average \
  --region "$REGION" \
  --query 'Datapoints[0].Average' \
  --output text)

echo "Baseline CPU: ${BASELINE_CPU}%"

# Install Apache Bench if not present
if ! command -v ab &> /dev/null; then
  echo -e "${YELLOW}Installing Apache Bench...${NC}"
  apt-get update && apt-get install -y apache2-utils
fi

# Run load test
echo -e "\n${BLUE}Running load test...${NC}"
echo "Testing http://${ALB_DNS}/health endpoint"
ab -t "$DURATION" -c "$CONCURRENCY" -r "http://${ALB_DNS}/health" > /tmp/load_test.txt

# Extract results
echo -e "\n${BLUE}Load Test Results:${NC}"
grep -E "Requests per second|Time per request|Failed requests|Successful requests" /tmp/load_test.txt

# Get post-test metrics
echo -e "\n${BLUE}Recording post-test metrics...${NC}"
POST_CPU=$(aws cloudwatch get-metric-statistics \
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

echo "Post-test CPU: ${POST_CPU}%"

# Check if scaling triggered
TASK_COUNT=$(aws ecs describe-services \
  --cluster settlement-ecs-cluster \
  --services settlement-service \
  --region "$REGION" \
  --query 'services[0].runningCount' \
  --output text)

echo "Running tasks: $TASK_COUNT"

# Determine pass/fail
PASS=true
if (( $(echo "$POST_CPU > 90" | bc -l) )); then
  echo -e "${YELLOW}⚠ CPU exceeded 90%${NC}"
  PASS=false
fi

if grep -q "Failed requests: [1-9]" /tmp/load_test.txt; then
  echo -e "${RED}✗ Some requests failed${NC}"
  PASS=false
fi

if [ "$PASS" = true ]; then
  echo -e "\n${GREEN}✓ Load test passed!${NC}"
  exit 0
else
  echo -e "\n${RED}✗ Load test failed - review metrics${NC}"
  exit 1
fi
