#!/bin/bash
set -e 

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

REGION=${AWS_REGION:-us-east-1}
LOG_GROUP="/ecs/settlement-pipeline"
SINCE=${1:-1h}

echo -e "${BLUE}Settlement Pipeline - Log Analysis${NC}"
echo "===================================="

# Parse time range
case "$SINCE" in
  1h) MINUTES=60 ;;
  2h) MINUTES=120 ;;
  12h) MINUTES=720 ;;
  24h) MINUTES=1440 ;;
  *) MINUTES=60 ;;
esac

echo -e "\n${BLUE}Analyzing logs from ladt $SINCE...${NC}"

# Query errors
echo -e "\n${BLUE}Recent ERROR logs:${NC}"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --region "$REGION" \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - MINUTES*60))000 \
  --query 'events[*].[timestamp,message]' \
  --output table | head -10

# Query warnings
echo -e "\n${BLUE}Recent WARNING logs:${NC}"
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --region "$REGION" \
  --filter-pattern "WARN" \
  --start-time $(($(date +%s) - MINUTES*60))000 \
  --query 'events[*].[timestamp,message]' \
  --output table | head -10

# Statistics
echo -e "\n${BLUE}Log Statistics (last $SINCE):${NC}"
aws logs start-query \
  --log-group-name "$LOG_GROUP" \
  --region "$REGION" \
  --start-time $(($(date +%s) - MINUTES*60))000 \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message, @logStream | stats count() as log_count by @logStream' \
  --output table | head table

echo -e "\n${GREEN}Analysis complete!${NC}"

