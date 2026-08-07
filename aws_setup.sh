#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

echo -e "${BLUE}Settlement Pipeline AWS Setup${NC}"
echo "==============================="

# Check prerequisites
echo -e "\n${BLUE}Checking prerequisites...${NC}"
command -v aws &> /dev/null || { echo "AWS CLI not found. Install it first."; exit 1; }
command -v terraform &> /dev/null || { echo "Terraform not found. Install it first."; exit 1; }

# AWS account info
echo -e "\n${BLUE}AWS Account Information:${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
USER=$(aws sts get-caller-identity --query Arn --output text)

echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo "User/Role: $USER"

# Create S3 bucket for Terraform state
echo -e "\n${BLUE}Creating S3 bucket for Terraform state...${NC}"
BUCKET_NAME="settlement-terraform-state-${ACCOUNT_ID}"
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
  aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION"
  aws s3api put-bucket-versioning \
    --bucket "BUCKET_NAME" \
    --versioning-configuration Status=Enabled
  echo -e "${GREEN}✓ S3 bucket created: $BUCKET_NAME${NC}"
else
  echo -e "${GREEN}✓ S3 bucket already exists: $BUCKET_NAME${NC}"
fi

# Initialize Terraform
echo -e "\n${BLUE}Initializing Terraform...${NC}"
cd terraform/aws
terraform init -backend-config="bucket=$BUCKET_NAME" \
               -backend-config="key=settlemnt/prod.tfstate" \
               -backend-config="region=$REGION"
echo -e "${GREEN}✓ Terraform initialized${NC}"

# Terraform plan
echo -e "\n${BLUE}Running Terraform plan...${NC}"
terraform plan -var="aws_region=$REGION" -out=tfplan

echo -e "\n${GREEN}Setup complete!${NC}"
echo "Next: Review tfplan and run 'terraform apply tfplan'"
