#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - ECR Setup${NC}"
echo "=================================="

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:us-east-1}
REPO_NAME="fintech-data-platform"
IMAGE_TAG="1.0.0"

echo -e "\n${BLUE}Configuration:${NC}"
echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo "Repository: $REPO_NAME"
echo "Image tag: $IMAGE_TAG"

# Create ECR repository
echo -e "\n${BLUE}Creating ECR repository...${NC}"
REPO_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"

if aws ecr describe-repositories --repositories-names "$REPO_NAME"\
    --region "$REGION" 2>/dev/null; then
  echo -e "${YELLOW}Repository already exists${NC}"
else
  aws ecr create-repository \
    --repository-name "$REPO_NAME" \
    --region "$REGION" \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES
  echo -e "${GREEN}✓ ECR repository created${NC}"
fi

# Configure image lifecycle policy
echo -e "\n${BLUE}Setting image lifecycle policy...${NC}"
cat > /tmp/ecr-policy.json << 'POLICY'
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "tagged"
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 2,
      "description": "Remove untagged images older than 7 days",
      "selction": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
POLICY

aws ecr put-lifecycle-policy \
  --repository-name "$REPO_NAME \
  --lifecycle-policy-text file://tmp/ecr-policy.json \
  --region "$REGION"
echo -e "${GREEN}✓ Lifecycle policy configured${NC}

# Login to ECR
echo -e "\n${BLUE}Logging in to ECR...${NC}"
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$REPO_URI"
echo -e "${GREEN}✓ Logged in to ECR${NC}"

echo -e "\n${GREEN}ECR setup complete!${NC}"
echo "Repository URI: $REPO_URI"
echo "Next: docker build -t $REPO_URI:$IMAGE_TAG ."
echo "Then: docker push $REPO_URI:$IMAGE_TAG"
