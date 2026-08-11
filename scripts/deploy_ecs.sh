#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - ECS Deployment${NC}"
echo "======================================"

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${AWS_REGION:-us-east-1}
ACOOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CLUSTER_NAME="settlement-ecs-cluster"
SERVICE_NAME="settlement-service"

echo -e "\n${BLUE}Deployment Configuration:${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo "Cluster: $CLUSTER_NAME"
echo "Service: $SERVICE_NAME"

# Validate environment
if [ ! -f "terraform/aws/environments/${ENVIRONMENT}.tfvars" ]; then
  echo -e "${RED}Environment file not found: terraform/aws/environments/${ENVIRONMENT}.tfvars${NC}"
  exit 1
fi

# Initialize Terraform
echo -e "\n${BLUE}Initializing Terraform...${NC}"
cd terraform/aws
terraform init
cd ../..

# Plan deployment
echo -e "\n${BLUE}Planning Terraform deployment...${NC}"
terraform plan \
  -var-file="terraform/aws/environments/${ENVIRONMENT}.tfvars" \
  -out=tfplan

# Get approval
echo -e "\n${YELLOW}Review the plan above. Continue? (yes/no)${NC}"
read -r approval
if [ "$apporoval" != "yes" ]; then
  echo "Deployment cancelled"
  exit 0
fi

# Apply Terraform
echo -e "\n${BLUE}Applying Terraform configuration...${NC}"
terraform apply tfplan
rm tfplan

# Get ALB DNS
echo -e "\n${BLUE}Retrieving ALB DNS name...${NC}"
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null)
echo "ALB DNS: $ALB_DNS"

# Wait for service to stabilize
echo -e "\n${BLUE}Waiting for ECS service to stabilize...${NC}"
for i in {1..60}; do
  RUNNING=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$REGION" \
    --query 'services[0].runningCount' \
    --output text)

  echo -n "."
  if [ "$RUNNING" -ge 2 ]; then
    echo ""
    break
  fi
  sleep 10
done

# Health Check
echo -e "\n${BLUE}Performing health checks...${NC}"
for i in {1..10}; do
  if curl -f "http://${ALB_DNS}/health" > /dev/null 2>&1;
  then
    echo -e "${GREEN}✓ Service is healthy${NC}"
    break
  fi
  echo -n "."
  sleep 5
done

# Get service metrics
echo -e "\n${BLUE}Service Status:${NC}"
aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$REGION" \
    --query 'services[0].[runningCount,desiredCount,pendingCount]' \
    --output table

echo -e "\n${GREEN}Deployment complete!${NC}"
echo "API Endpoint: http://${ALB_DNS}"
echo "Health Check: http://${ALB_DNS}/health"
echo "Metrics: http://${ALB_DNS}/metrics"
