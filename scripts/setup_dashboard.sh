#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - Dashboard Setup${NC}"
echo "======================================"

CLUSTER="settlement-ecs-cluster"
REGION="us-east-1"

# Create CloudWatch Dashboard JSON
cat > /tmp/dashboard.json << 'DASHBOARD'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
          [".", "MemoryUtilization", {"stat": "Average"}]
        ],
        "period": 60,
        "stat": "Average",
        "region": "us-east-1",
        "title": "ECS Resource Utilization"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", {"stat": "Average"}],
          [".", "HTTPCode_Target_5XX_Count", {"stat": "Sum"}]
        ],
        "period": 60,
        "stat": "Average",
        "region": "us-east-1",
        "title": "ALB Health"
      }
    }
  ]
}
DASHBOARD

echo -e "${GREEN}✓ Dashboard configuration ready${NC}"
echo "Dashboard JSON: /tmp/dashboard.json"

# Create the dashboard
aws cloudwatch put-dashboard \
  --dashboard-name settlement-live \
  --dashboard-body file:///tmp/dashboard.json \
  --region "$REGION"

echo -e "${GREEN}✓ Dashboard created in CloudWatch${NC}"
echo "URL: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=settlement-live"
