#!/bin/bash
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

IMAGE=${1:-fintech-data-platform:latest}

echo -e "${BLUE}Verifying Docker Image: {$IMAGE${NC}}"
echo "========================================"

# 1. Check image exists
echo -e "\n${BLUE}1. Checking image exists...${NC}"
if docker image inspect "$IMAGE" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Image found${NC}"
else
  echo "Image not found"
  exit 1
fi

# 2. Check image size
echo -e "\n${BLUE}2. Checking image size...${NC}"
SIZE=$(docker image inspect "$IMAGE" --format='{{.Size}}' | numfmt --to=iec)
echo "Image size: $SIZE"
if (( $(echo "$(docker image inspect "$IMAGE" --format='{{.Size}}')" ">" 1000000000 | bc -l) )); then
  echo -e "${YELLOW}⚠ Image larger than 1GB${NC}"
fi

# 3. Test image startup
echo -e "\n${BLUE}3.Testing image startup...${NC}"
docker run --rm -d --name test-"$$" "$IMAGE" > /dev/null
sleep 3
if docker ps | grep -q test-"$$"; then
  docker stop test-"$$" > /dev/null
  echo -e "${GREEN}✓ Image starts successfully${NC}"
else
  echo -e "Image failed to start"
  exit 1
fi

# 4. Check for secrets in image
echo -e "\n${BLUE}4. Scanning for secrets...${NC}"
if docker inspect "$IMAGE" | grep -i "secret\|password\|apikey\|token" 2>/dev/null; then
  echo -e "${YELLOW}⚠ Potential secrets found in image${NC}"
else
  echo -e "${GREEN}✓ No obvious secrets detected${NC}"
fi

# 5. Check layers
echo -e "\n${BLUE}5. Image layers:${NC}"
docker image history "$IMAGE" --no-trunc --human | head -10

echo -e "\n${GREEN}Verification complete!${NC}"
