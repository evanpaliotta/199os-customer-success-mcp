#!/bin/bash
# ==============================================================================
# Docker Image Verification Script
# Tests the production-ready Docker setup
# ==============================================================================

set -e

echo "=========================================="
echo "Docker Image Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker daemon
echo "1. Checking Docker daemon..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker daemon is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"
echo ""

# Build the image
echo "2. Building production Docker image..."
START_BUILD=$(date +%s)
docker build -t cs-mcp:production .
END_BUILD=$(date +%s)
BUILD_TIME=$((END_BUILD - START_BUILD))
echo -e "${GREEN}✓ Build completed in ${BUILD_TIME}s${NC}"
echo ""

# Check image size
echo "3. Checking image size..."
IMAGE_SIZE=$(docker images cs-mcp:production --format "{{.Size}}")
IMAGE_SIZE_MB=$(docker images cs-mcp:production --format "{{.Size}}" | sed 's/MB//' | awk '{print int($1)}')
echo "   Image size: ${IMAGE_SIZE}"
if [ "$IMAGE_SIZE_MB" -lt 500 ]; then
    echo -e "${GREEN}✓ Image size is under 500MB target${NC}"
else
    echo -e "${YELLOW}⚠ Image size exceeds 500MB target${NC}"
fi
echo ""

# Verify non-root user
echo "4. Verifying non-root user..."
USER_CHECK=$(docker run --rm cs-mcp:production whoami)
if [ "$USER_CHECK" = "csops" ]; then
    echo -e "${GREEN}✓ Container runs as non-root user 'csops'${NC}"
else
    echo -e "${RED}✗ Container runs as user: $USER_CHECK (should be csops)${NC}"
fi
echo ""

# Verify UID
echo "5. Verifying UID..."
UID_CHECK=$(docker run --rm cs-mcp:production id -u)
if [ "$UID_CHECK" = "1000" ]; then
    echo -e "${GREEN}✓ Container UID is 1000${NC}"
else
    echo -e "${RED}✗ Container UID is $UID_CHECK (should be 1000)${NC}"
fi
echo ""

# Check for build tools in runtime image (should not exist)
echo "6. Verifying build tools are removed..."
if docker run --rm cs-mcp:production which gcc > /dev/null 2>&1; then
    echo -e "${RED}✗ Build tools found in runtime image (gcc present)${NC}"
else
    echo -e "${GREEN}✓ Build tools removed from runtime image${NC}"
fi
echo ""

# Verify Python packages installed
echo "7. Verifying Python packages..."
FASTMCP_CHECK=$(docker run --rm cs-mcp:production pip show fastmcp > /dev/null 2>&1 && echo "found" || echo "missing")
if [ "$FASTMCP_CHECK" = "found" ]; then
    echo -e "${GREEN}✓ Python packages installed correctly${NC}"
else
    echo -e "${RED}✗ Required Python packages missing${NC}"
fi
echo ""

# Test health check command
echo "8. Testing health check command..."
docker run --rm --name cs-mcp-health-test -d -p 8080:8080 \
    -e DATABASE_URL="" -e REDIS_URL="" cs-mcp:production
sleep 3
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' cs-mcp-health-test 2>/dev/null || echo "no-healthcheck")
docker stop cs-mcp-health-test > /dev/null 2>&1 || true
if [ "$HEALTH_STATUS" != "no-healthcheck" ]; then
    echo -e "${GREEN}✓ Health check is configured${NC}"
else
    echo -e "${YELLOW}⚠ Health check status: $HEALTH_STATUS${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Build time: ${BUILD_TIME}s"
echo "Image size: ${IMAGE_SIZE}"
echo "User: ${USER_CHECK} (UID: ${UID_CHECK})"
echo ""
echo -e "${GREEN}Docker image verification complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start services: docker-compose up -d"
echo "2. Check health: docker-compose ps"
echo "3. View logs: docker-compose logs -f customer-success-mcp"
echo "4. Test MCP connection"
