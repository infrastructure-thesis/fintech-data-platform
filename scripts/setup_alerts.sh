#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

REGION=${AWS_REGION:-us-east-1}
SNS_TOPIC="settlement-alerts"

echo -e "${BLUE}Settlment Pipeline - Alert Setup${NC}"
echo "==================================="

# Get SNS topic ARN
echo -e "\n${BLUE}Retrieving SNS topic...${NC}"
TOPIC_ARN=$(aws sns list-topics --region "$REGION" \
  -query "Topics[?TopicArn contains('${SNS_TOPIC}')] | [0].TopicArn" \
  --output text)

if [ -z "$TOPIC_ARN" ] || [ "$TOPIC_ARN" = "None" ]; then
  echo -e "${YELLOW}SNS topic not found. Creating...${NC}"
  TOPIC_ARN=$(aws sns create-topic --name "$SNS_TOPIC" --region "$REGION \
  -query 'TopicArn' --output text)
fi

echo "Topic ARN: $TOPIC_ARN

# List subscriptions
echo -e "\n${BLUE}Current subscriptions:${NC}"
aws sns list-subscritpions-by-topic \
  --topic-arn "$TOPIC_ARN" \
  --region "$REGION" \
  --query 'Subscriptions[].[Endpoint,SubscriptionArn]' \
  --output table

# Add email subscription (if provided)
if [ -n "$ALERT_EMAIL" ]; then
  echo -e "\n${BLUE}Subscribing email: $ALERT_EMAIL${NC}"
  aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol email \
    --notification-endpoint "$ALERT_EMAIL" \
    --region "$REGION"
  echo -e "\n${GREEN}✓ Email subscription created (check email for confirmation)${NC}"
fi

# Add Slack webhook (if provided)
if [ -n "$SLACK_WEBHOOK" ]; then
  echo -e "\n${BLUE}Configuring Slack integration...${NC}"

  # Create Lambda function for Slack
  cat > /tmp/lambda_function.py << 'LAMBDA'
import json
import urllib3
import os

http = urllib3.PoolManager()
SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    alarm_name = message.get('AlarmName', 'Unknown')
    new_state = message.get('NewStateValue', 'Unknown')
    reason = message.get('NewStateReason', '')

    slack_message = {
        'text': f"🚨 AWS Alert: {alarm_name}",
        'attachments': [
            {
                'color': 'danger' if new_state == 'ALARM' else 'good',
                'fields': [
                    {'title': 'Alarm', 'value': alarm_name, 'short': True},
                    {'title': 'State', 'value': new_state, 'short': True},
                    {'title': 'Reason', 'value': reason, 'short': False}
                  ]
            }
        ]
    }

    encoded_msg = json.dumps(slack_message).encode('utf-8')
    resp = http.request('POST', SLACK_WEBHOOK, body=encoded_msg)
    return {'statusCode' : 200}
LAMBDA

  echo -e "\n${GREEN}Alert setup complete!${NC}"
  echo "Topic ARN: $TOPIC_ARN"
  echo "Dashboard: https://console.aws.amazonaws.com/cloudwatch/home?region=${REGION}#dashboards:name=settlement-pipeline"
