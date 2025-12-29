#!/bin/bash
# infra/scripts/migrate.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 Running database migrations...${NC}"

# Get EC2 instance IP from Terraform
cd "$(dirname "$0")/../terraform"
EC2_IP=$(terraform output -raw instance_public_ip 2>/dev/null)

if [ -z "$EC2_IP" ]; then
    echo -e "${RED}❌ Could not get EC2 instance IP from Terraform${NC}"
    echo "Make sure you've run 'terraform apply' first"
    exit 1
fi

echo -e "${YELLOW}📡 Connecting to: $EC2_IP${NC}"

# Run migrations on EC2
ssh -o StrictHostKeyChecking=no -i ~/.ssh/species-tracker ubuntu@$EC2_IP << 'ENDSSH'
set -e

echo "Running migrations..."
cd /opt/species-tracker
docker exec species-backend python manage.py migrate

echo "Collecting static files..."
docker exec species-backend python manage.py collectstatic --noinput

echo "✅ Migrations completed successfully!"
ENDSSH

echo -e "${GREEN}✅ Migrations completed successfully!${NC}"
