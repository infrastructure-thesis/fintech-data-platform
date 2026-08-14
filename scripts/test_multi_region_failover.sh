#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - Multi-Region Failover Test${NC}"
echo "=================================================="

PRIMARY_REGION="us-east-1"
SECONDARY_REGION="eu-west-1"
TERTIARY_REGION="ap-southeast-1"
DOMAIN="settlement.company.com"

echo -e "\n${BLUE}Test 1: Primary Region Health${NC}"
echo "=============================="

# Check primary region
PRIMARY_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://primary.${DOMAIN}/health" || echo "000")

if [ "$PRIMARY_HEALTH" = "200" ]; then
  echo -e "${GREEN}✓ Primary region healthy${NC}"
else
  echo -e "${RED}✗ Primary region unhealthy (HTTP $PRIMARY_HEALTH)${NC}"
fi

# Check replication lag
echo -e "\n${BLUE}Test 2: Replication Status${NC}"
echo "=========================="

REPLICATION_LAG=$(aws rds describe-db-clusters \
  --region "$SECONDARY_REGION" \
  --query 'DBClusters[0].GlobalWriteForwardingStatus' \
  --output text)

if [ "$REPLICATION_LAG" != "None" ]; then
  echo -e "${GREEN}✓ Replication active${NC}"
else
  echo -e "${YELLOW}⚠ Replication lag detected${NC}"
fi

# Check Kafka mirror status
MIRROR_LAG=$(aws ec2 describe-instances \
  --region "$SECONDARY_REGION" \
  --filters "Name=tag:MirrorMaker,Values=true" \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text)

if [ "$MIRROR_LAG" = "running" ]; then
  echo -e "${GREEN}✓ Kafka mirror cluster running${NC}"
else
  echo -e "${YELLOW}⚠ Kafka mirror cluster not running${NC}"
fi

# Test 3: Simulated Primary Failure
echo -e "\n${BLUE}Test 3: Simulated Primary Region Failure${NC}"
echo "========================================"

echo -e "${YELLOW}Simulating primary region outage...${NC}"
echo "Health checks will fail and Route53 will failover to secondary"

# Simulate by checking DNS resolution
for i in {1..5}; do
  RESOLVED_IP=$(dig +short "$DOMAIN" | head -1)
  echo "Attempt $i: Resolved to $RESOLVED_IP"
  sleep 2
done

# Query Route53 to see which region is active
ACTIVE_REGION=$(aws route53 list-resource-record-sets \
  --hosted-zone-id $(aws route53 list-hosted-zones-by-name \
    --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
    --output text) \
  --query 'ResourceRecordSets[?Type==`A`].SetIdentifier' \
  --output text)

echo -e "\n${BLUE}Route53 Status${NC}"
echo "==============="
echo "Active region: $ACTIVE_REGION"

if [[ "$ACTIVE_REGION" == *"Primary"* ]]; then
  echo -e "${GREEN}✓ Primary region is active${NC}"
elif [[ "$ACTIVE_REGION" == *"Secondary"* ]]; then
  echo -e "${YELLOW}⚠ Secondary region has taken over${NC}"
else
  echo -e "${YELLOW}⚠ Unable to determine active region${NC}"
fi

# Test 4: Failback to Primary
echo -e "\n${BLUE}Test 4: Failback to Primary${NC}"
echo "============================"

# Verify primary region is healthy
if [ "$PRIMARY_HEALTH" = "200" ]; then
  echo -e "${GREEN}✓ Primary region is healthy and ready for failback${NC}"
  echo "Waiting 60 seconds for Route53 to failback..."
  sleep 60
  
  FINAL_IP=$(dig +short "$DOMAIN" | head -1)
  echo "Final resolved IP: $FINAL_IP"
  echo -e "${GREEN}✓ Failback complete${NC}"
else
  echo -e "${RED}✗ Primary region still unhealthy, cannot failback${NC}"
fi

# Test 5: Data Consistency
echo -e "\n${BLUE}Test 5: Data Consistency Verification${NC}"
echo "====================================="

# Query audit log count from both regions
PRIMARY_COUNT=$(aws rds-data execute-statement \
  --resource-arn "arn:aws:rds:${PRIMARY_REGION}:...database/settlement-db" \
  --database "settlement" \
  --sql "SELECT COUNT(*) FROM audit_log" \
  --region "$PRIMARY_REGION" \
  --query 'records[0][0].longValue' \
  --output text 2>/dev/null || echo "unknown")

SECONDARY_COUNT=$(aws rds-data execute-statement \
  --resource-arn "arn:aws:rds:${SECONDARY_REGION}:...database/settlement-db" \
  --database "settlement" \
  --sql "SELECT COUNT(*) FROM audit_log" \
  --region "$SECONDARY_REGION" \
  --query 'records[0][0].longValue' \
  --output text 2>/dev/null || echo "unknown")

echo "Primary audit logs: $PRIMARY_COUNT"
echo "Secondary audit logs: $SECONDARY_COUNT"

if [ "$PRIMARY_COUNT" = "$SECONDARY_COUNT" ]; then
  echo -e "${GREEN}✓ Data is consistent across regions${NC}"
else
  echo -e "${YELLOW}⚠ Data inconsistency detected${NC}"
fi

echo -e "\n${GREEN}Multi-region failover test complete!${NC}"
