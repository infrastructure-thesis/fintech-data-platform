#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Settlment Pipeline - Docker Build & Push${NC}"
echo "=========================================="

# Configuration
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}
REPO_NAME="fintech-data-platform"
IMAGE_TAG=${1:-1.0.0}
REPO_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"

echo -e "\n${BUILD}Build Configuration:${NC}"
echo "Repository URI: $REPO_URI"
echo "Image tag: $IMAGE_TAG"

# Build Docker image
echo -e "\n${BLUE}Building Docker image...${NC}"
docker build \
  --tag "$REPO_URI:$IMAGE_TAG" \
  --tag "$REPO_URI:latest" \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  .

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
  echo -e "${RED}✗ Docker build failed${NC}"
  exit 1
fi

# Check image size
echo -e "\n${BLUE}Image information:${NC}"
docker images "$REPO_URI" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Run security scan locally (if trivy installed)
if command -v trivy &> /dev/null; then
  echo -e "\n${BLUE}Running Trivy security scan...${NC}"
  trivy image "$REPO_URI:$IMAGE_TAG" || true
fi

# Login to ECR
echo -e "\n${BLUE}Logging in to ECR...${NC}"
aws ecr get-login-password --region "$REGION" |\
  docker login --username AWS --password-stdin "REPO_URI"
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Push image to ECR
echo -e "\n${BLUE}Pushing image to ECR...${NC}"
docker push "$REPO_URI:$IMAGE_TAG"
docker push "$REPO_URI:latest"
echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Get image digest
echo -e "\n${BLUE}Image Details:${NC}"
DIGEST=$(docker inspect --format='{{.RepoDigests}}' "$REPO_URI:$IMAGE_TAG" | grep -oP 'sha256:\K[a-f0-9]{64}' | head -1)
echo "Image URI: $REPO_URI:$IMAGE_TAG"
echo "Digest: $DIGEST"

echo -e "\n${GREEN}Build and push complete!${NC}"
