# PagerDuty Integration Guide

## Setup Steps

## 1. Create PagerDuty Service
1. Log in to PagerDuty
2. Navigate to Services → New Service
3. Name: "Settlement Pipeline"
4. Escalation Poilcy: Select appropriate policy
5. Alert Creation: Events from AWS CloudWatch
6. Copy Integration Key (you'll need this)

### 2. Create SNS-to-PagerDuty Lambda

```bash
# Create Lambda execution role
aws iam create-role --role-name PagerDutyLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts.AssumeRole"
    }]
  }'

# Attach basic execution policy
aws iam attach-role-policy \
  --role-name PagerDutyLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### 3. Lambda Function Code

```python
import json
import urllib3
import os

http = urllib3.PoolManager()
PAGERDUTY_KEY = os.environ['PAGERDUTY_INTEGRATION_KEY']
PAGERDUTY_URL = 'https://events.pagerduty.com/v2/enqueue'

def lambda_handler(event, context):
    message = json.loads(event['Records][0]['Sns]['Message])

    alarm_name = message.get('AlarmName', 'Unknown Alarm')
    new_state = message.get('NewStateValue', 'UNKNOWN')
    old_state = message.get('OldStateValue', 'UNKNOWN')
    reason = message.get('NewStateReason', 'No reason provided')

    # Determine severity
    severity_map = {
        'ALARM': 'critical',
        'INSUFFICIENT_DATA': 'warning',
        'OK': 'info'
    }
    severity = severity_map.get(new_state, 'error')

    # Determine action
    action = 'resolve' if new_state == 'OK' else 'trigger'

    pagerduty_event = {
        'routing_key': PAGERDUTY_KEY,
        'event_action': action,
        'dedup_key': alarm_name,
        'payload': {
            'summary': f"{alarm_name}:{new_state}",
            'severity': severity,
            'source': 'AWS CloudWatch',
            'custom_details': {
                'alarm_name': alarm_name,
                'state_transition': f"{old_state} → {new_state}",
                'reason': reason
            }
        }
    }

    encoded_msg = json.dumps(pagerduty_event).encode('utf-8')
    resp = http.request('POST', PAGERDUTY_URL, body=encoded_msg)

    return {
        'statusCode': resp.status,
        'body': json.dumps({'message': 'Event sent to PagerDuty'})
    }
```

### 4. Deploy Lambda Function

```bash
# Package function
zip lambda_function.zip lambda_function.py

# Create function
aws lambda create-function \
  --function-name CloudWatchToPagerDuty \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/PagerDutyLambdaRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --environment Variables={PAGERDUTY_INTEGRATION_KEY=your_integration_key}

# Get function ARN
LAMBDA_ARN=$(aws lambda get-function --function-name CloudWatchToPagerDuty \
  --query 'Configuration.FunctionArn' --output text)
```

### 5. Connect SNS to Lambda

```bash
# Add SNS trigger to Lambda
aws sns subscribe \
  --topic-arn arn:aws:sns::REGION:ACCOUNT_ID:settlement-alerts \
  --protocol lambda \
  --notification-endpoint $LAMBDA_ARN

# Allow SNS to invoke Lambda
aws lambda add-permission \
  --function-name CloudWatchToPagerDuty \
  --statement-id AllowSNS \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:REGION:ACCOUNT_ID:settlement-alerts
```

## Alert Routing

### Critical Alerts
- CPU > 90%
- Memory > 95%
- 5xx errors > 20 in 5min
- **Action:** Immediate PagerDuty alert, page on-call

### Warning Alerts
- CPU > 80%
- Memory > 85%
- Response time > 500ms
- **Action:** SNS email + Slack notification

### Info Alerts
- Scaling events
- Deployment changes
- **Action**: Slack #ops channel only

## Testing

```bash
# Trigger test alert
aws cloudwatch set-alarm-state \
  --alarm-name settlement-ecs-cpu-high \
  --state-value ALARM \
  --state-reason "Test alert"

# Check PagerDuty dashboard for incident
```

## Escalation Policy

1. **L1 (30 min):** On-call engineer
2. **L2 (30 min):** Team lead
3. **L3 (30 min):** Platform engineering manager

## Acknowledging/Resolve

Incidents auto-resolve when alarm returns to OK state.

Manual resolution:

```bash
aws cloudwatch set-alarm-state \
  --alarm-name settlement-ecs-cpu-high \
  --state-value OK \
  --state-reason "Issue resolved"
```
