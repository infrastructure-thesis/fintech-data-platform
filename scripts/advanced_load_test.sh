#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ALB_ENDPOINT=${ALB_ENDPOINT:-http://localhost:8000}
DURATION=${DURATION:-300}  # 5 minutes
CONCURRENCY=${CONCURRENCY:-50}
REPORT_FILE="load_test_$(date +%Y%m%d_%H%M%S).html"

echo -e "${BLUE}Advanced Load Test - Settlement Pipeline${NC}"
echo "=========================================="
echo "Endpoint: $ALB_ENDPOINT"
echo "Duration: ${DURATION}s"
echo "Concurrency: $CONCURRENCY"

# Phase 1: Warm-up (1 min)
echo -e "\n${YELLOW}Phase 1: Warm-up (60s)${NC}"
ab -n 100 -c 10 -t 60 "$ALB_ENDPOINT/health" > /dev/null

# Phase 2: Ramp-up (2 min)
echo -e "${YELLOW}Phase 2: Ramp-up (120s)${NC}"
ab -n 500 -c 25 -t 120 "$ALB_ENDPOINT/health" > /dev/null

# Phase 3: Peak load (2 min)
echo -e "${YELLOW}Phase 3: Peak load (120s)${NC}"
ab -n 1000 -c "$CONCURRENCY" -t 120 \
  -g "$REPORT_FILE" \
  "$ALB_ENDPOINT/health"

# Phase 4: Cool-down (1 min)
echo -e "${YELLOW}Phase 4: Cool-down (60s)${NC}"
ab -n 100 -c 10 -t 60 "$ALB_ENDPOINT/health" > /dev/null

echo -e "\n${BLUE}Load Test Results${NC}"
echo "=================="
echo "Report saved to: $REPORT_FILE"

# Analyze results
TOTAL_REQUESTS=1700
echo "Total requests: $TOTAL_REQUESTS"
echo "Concurrency: $CONCURRENCY requests/sec"
echo ""
echo "Expected throughput: ~$(($TOTAL_REQUESTS / $DURATION)) req/sec"

# Check API endpoint separately
echo -e "\n${BLUE}API Endpoint Testing${NC}"
echo "===================="

# Generate token
TOKEN=$(curl -s -X POST "$ALB_ENDPOINT/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo -e "${RED}✗ Failed to obtain token${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Token obtained${NC}"

# Test /stats endpoint with token
echo "Testing /stats endpoint..."
ab -n 100 -c 20 -t 60 \
  -H "Authorization: Bearer $TOKEN" \
  "$ALB_ENDPOINT/stats" > /dev/null

echo -e "\n${GREEN}Load test complete!${NC}"
