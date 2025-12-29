#!/bin/bash
# infra/scripts/deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-eu-west-3}

echo -e "${GREEN}🚀 Starting deployment for Marine Species Tracker${NC}"

# Get EC2 instance IP from Terraform
cd "$(dirname "$0")/../terraform"
EC2_IP=$(terraform output -raw instance_public_ip 2>/dev/null)

if [ -z "$EC2_IP" ]; then
    echo -e "${RED}❌ Could not get EC2 instance IP from Terraform${NC}"
    echo "Make sure you've run 'terraform apply' first"
    exit 1
fi

echo -e "${YELLOW}📡 Deploying to: $EC2_IP${NC}"

# Get to repo root
cd "$(dirname "$0")/../.."

# Step 1: Build images locally
echo -e "${YELLOW}🔨 Building Docker images...${NC}"

echo "Building backend..."
cd backend
docker build --platform linux/amd64 -t backend:latest .

echo "Building frontend..."
cd ../frontend
docker build --platform linux/amd64 -t frontend:latest .

# Step 2: Save images to tar files
echo -e "${YELLOW}💾 Saving images...${NC}"
cd ..
docker save backend:latest | gzip > /tmp/backend.tar.gz
docker save frontend:latest | gzip > /tmp/frontend.tar.gz

# Step 3: Copy images to EC2
echo -e "${YELLOW}📤 Uploading images to EC2...${NC}"
scp -o StrictHostKeyChecking=no -i ~/.ssh/species-tracker \
    /tmp/backend.tar.gz ubuntu@$EC2_IP:/tmp/
scp -o StrictHostKeyChecking=no -i ~/.ssh/species-tracker \
    /tmp/frontend.tar.gz ubuntu@$EC2_IP:/tmp/

# Step 4: Load images on EC2 and deploy
echo -e "${YELLOW}🚀 Loading images and deploying on EC2...${NC}"
ssh -o StrictHostKeyChecking=no -i ~/.ssh/species-tracker ubuntu@$EC2_IP << 'ENDSSH'
set -e

echo "Loading backend image..."
sudo docker load < /tmp/backend.tar.gz

echo "Loading frontend image..."
sudo docker load < /tmp/frontend.tar.gz

echo "Cleaning up temporary files..."
rm /tmp/backend.tar.gz /tmp/frontend.tar.gz

echo "Deploying application..."
cd /opt/species-tracker
sudo ./deploy.sh

echo "✅ Deployment complete!"
ENDSSH

# Clean up local tar files
rm /tmp/backend.tar.gz /tmp/frontend.tar.gz

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Frontend: https://species.kuroshio-lab.com${NC}"
echo -e "${GREEN}🔌 API: https://api.species.kuroshio-lab.com${NC}"
echo ""
echo -e "${YELLOW}To view logs, SSH into the instance:${NC}"
echo -e "ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP"
echo -e "cd /opt/species-tracker && docker-compose logs -f"
