#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Webhook Delivery Configuration${NC}"
echo "==============================="

# Example: Setup webhook for customer
CUSTOMER_ID="acme-corp"
WEBHOOK_URL="https://acme.com/webhooks/settlement"
WEBHOOK_SECRET="whk_secret_12345"

echo -e "\n${BLUE}Registering webhook:${NC}"
echo "Customer: $CUSTOMER_ID"
echo "URL: $WEBHOOK_URL"
echo "Secret: $WEBHOOK_SECRET"

# Create webhook in customer account
# (Would be done via dashboard in production)
echo -e "\n${GREEN}✓ Webhook registered${NC}"

# Test webhook delivery
echo -e "\n${BLUE}Testing webhook delivery:${NC}"

EVENT_PAYLOAD='{"id":"evt_001","type":"transaction.processed","tenant_id":"acme-corp","timestamp":"2026-08-27T11:30:00Z","data":{"transaction_id":"txn_001","status":"success","amount":"1000.50"}}'

SIGNATURE=$(echo -n "$EVENT_PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d' ' -f2)

curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Settlement-Signature: $SIGNATURE" \
  -H "X-Settlement-Event-Type: transaction.processed" \
  -H "X-Settlement-Event-ID: evt_001" \
  -d "$EVENT_PAYLOAD"

echo -e "\n${GREEN}✓ Webhook test sent${NC}"
