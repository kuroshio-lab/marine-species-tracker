# Marine Species Tracker - Deployment Guide (EC2)

Simple, cost-effective deployment guide using a single EC2 instance.

## Architecture

```
Route53 → EC2 Instance (t3.small)
           ├─ Nginx (HTTPS with Let's Encrypt)
           ├─ Backend (Django in Docker)
           ├─ Frontend (Next.js in Docker)
           └─ → RDS PostgreSQL
```

**Monthly Cost: ~$35**
- EC2 t3.small: ~$15
- RDS db.t4g.micro: ~$15
- EBS storage: ~$3
- Route53 + data transfer: ~$2

## Prerequisites

1. ✅ Global infrastructure deployed (from `infra` repo)
2. ✅ AWS CLI configured
3. ✅ Terraform >= 1.0 installed
4. ✅ Docker installed locally
5. ✅ Resend account and API key
6. ✅ SSH key pair generated

## Step 1: Generate SSH Key

```bash
# Generate new SSH key for EC2 access
ssh-keygen -t rsa -b 4096 -f ~/.ssh/species-tracker -C "species-tracker"

# View public key (you'll need this for terraform)
cat ~/.ssh/species-tracker.pub
```

## Step 2: Configure Terraform Variables

```bash
cd infra/terraform
cp personal.tfvars.example personal.tfvars
```

Edit `personal.tfvars`:

```hcl
aws_region  = "eu-west-3"
environment = "production"

# EC2 settings
instance_type = "t3.micro"
volume_size   = 30

# Database settings
db_instance_class = "db.t3.micro"

# SSH configuration
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..."  # Paste your public key
ssh_allowed_ips = ["YOUR_IP/32"]  # Your IP only (for security)

# Secrets
resend_api_key = "re_YOUR_ACTUAL_API_KEY"
```

**Security Note:** Replace `YOUR_IP/32` with your actual IP address for SSH access!

## Step 3: Deploy Infrastructure

```bash
terraform init
terraform plan -var-file="personal.tfvars"
terraform apply -var-file="personal.tfvars"
```

⏱️ **Time:** 10-15 minutes

**What gets created:**
- VPC with public subnets
- EC2 instance with Docker installed
- RDS PostgreSQL database
- Security groups
- Elastic IP (static IP address)
- Route53 DNS records

## Step 4: Verify EC2 Setup

```bash
# Get EC2 IP
EC2_IP=$(terraform output -raw instance_public_ip)

# SSH into instance
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

# Check if setup is complete
sudo cat /root/SETUP_COMPLETE

# Exit SSH
exit
```

## Step 5: Setup SSL Certificates (First Time Only)

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

# Setup Let's Encrypt SSL
cd /opt/species-tracker
sudo ./setup-ssl.sh

# This will:
# 1. Start nginx
# 2. Request SSL certificates from Let's Encrypt
# 3. Install certificates for both domains
# 4. Restart nginx with SSL enabled

# Exit SSH
exit
```

⏱️ **Time:** 2-3 minutes

## Step 6: Deploy Application

From your local machine:

```bash
cd infra/scripts
chmod +x deploy.sh migrate.sh

# Build and deploy
./deploy.sh
```

⏱️ **Time:** 5-10 minutes

**What happens:**
1. Builds Docker images locally
2. Uploads images to EC2
3. Loads images on EC2
4. Starts containers with docker-compose
5. Nginx routes traffic to containers

## Step 7: Run Database Migrations

```bash
./migrate.sh
```

⏱️ **Time:** 1-2 minutes

## Step 8: Create Admin User

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

# Create superuser
cd /opt/species-tracker
docker exec -it species-backend python manage.py createsuperuser

# Enter username, email, and password

# Exit SSH
exit
```

## Step 9: Verify Deployment

### Check Services

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

cd /opt/species-tracker

# Check container status
docker-compose ps

# Expected output:
# NAME                  STATUS              PORTS
# species-backend       Up (healthy)        8000/tcp
# species-frontend      Up                  3000/tcp
# species-nginx         Up                  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp

# View logs
docker-compose logs -f
```

### Test Endpoints

**Frontend:** https://species.kuroshio-lab.com
- ✅ Page loads
- ✅ No SSL warnings
- ✅ Can navigate

**API Health:** https://api.species.kuroshio-lab.com/health/
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "environment": "ok",
    "s3": "configured"
  }
}
```

**API Docs:** https://api.species.kuroshio-lab.com/api/schema/swagger/

**Admin Panel:** https://api.species.kuroshio-lab.com/admin/

## Common Operations

### Update Application Code

```bash
cd infra/scripts
./deploy.sh
```

### View Logs

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

cd /opt/species-tracker

# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Nginx only
docker-compose logs -f nginx
```

### Restart Services

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

cd /opt/species-tracker

# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart nginx
```

### Run Django Management Commands

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

cd /opt/species-tracker

# Django shell
docker exec -it species-backend python manage.py shell

# Create superuser
docker exec -it species-backend python manage.py createsuperuser

# Collect static files
docker exec species-backend python manage.py collectstatic --noinput

# Run migrations
docker exec species-backend python manage.py migrate
```

### Update Infrastructure

```bash
cd infra/terraform

# Review changes
terraform plan -var-file="personal.tfvars"

# Apply changes
terraform apply -var-file="personal.tfvars"
```

### Scale EC2 Instance

Edit `personal.tfvars`:
```hcl
instance_type = "t3.medium"  # Upgrade to 4GB RAM
```

Apply:
```bash
terraform apply -var-file="personal.tfvars"
```

**Note:** This will cause downtime as the instance is replaced!

## Backup and Restore

### Database Backup

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

# Create backup
docker exec species-backend python manage.py dumpdata > /tmp/backup-$(date +%Y%m%d).json

# Download backup
exit
scp -i ~/.ssh/species-tracker ubuntu@$EC2_IP:/tmp/backup-*.json ./
```

**Note:** RDS automatically creates daily backups (7-day retention).

### Restore from Backup

```bash
# Upload backup to EC2
scp -i ~/.ssh/species-tracker backup-20250101.json ubuntu@$EC2_IP:/tmp/

# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

# Restore
docker exec -i species-backend python manage.py loaddata < /tmp/backup-20250101.json
```

## Monitoring

### Check Resource Usage

```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

# CPU and memory
top

# Disk usage
df -h

# Docker stats
docker stats

# Container resource usage
docker-compose stats
```

### CloudWatch Metrics

Check AWS Console → CloudWatch:
- EC2 CPU utilization
- RDS CPU utilization
- RDS storage space
- Custom alarms configured

## SSL Certificate Renewal

Let's Encrypt certificates auto-renew every 12 hours via the certbot container.

To manually renew:
```bash
# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

cd /opt/species-tracker
docker-compose run --rm certbot renew
docker-compose restart nginx
```

## Troubleshooting

### 502 Bad Gateway

**Check backend status:**
```bash
docker-compose ps backend
docker-compose logs backend
```

**Common causes:**
- Backend container not running
- Backend health check failing
- Database connection issues

### SSL Certificate Issues

**Check certificate status:**
```bash
docker-compose logs certbot
ls -la /opt/species-tracker/ssl
```

**Manually request certificates:**
```bash
sudo ./setup-ssl.sh
```

### Database Connection Failed

**Check RDS status:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier species-tracker-postgres \
  --region eu-west-3 \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Check security group:**
```bash
# From EC2, test connection
docker exec species-backend python manage.py check --database default
```

### Out of Disk Space

**Check disk usage:**
```bash
df -h
docker system df
```

**Clean up:**
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Clean Docker system
docker system prune -a --volumes
```

### Container Won't Start

**Check logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Common issues:**
- Environment variables not set
- Port conflicts
- Out of memory
- Image not built correctly

**Solution:**
```bash
# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## Cost Optimization

Current setup: **~$35/month**

### Reduce Costs Further

1. **Use t3.micro** (~$7/month): Good for very low traffic
   ```hcl
   instance_type = "t3.micro"
   ```

2. **Stop instance when not needed**: EC2 charges hourly
   ```bash
   aws ec2 stop-instances --instance-ids i-xxxxx
   aws ec2 start-instances --instance-ids i-xxxxx
   ```

3. **Use RDS free tier**: db.t3.micro (1 year free)
   ```hcl
   db_instance_class = "db.t3.micro"
   ```

**Minimal setup: ~$7-10/month** (t3.micro EC2 only, no RDS)

### Scale Up for Production

1. **Larger instance**: t3.medium ($30/month)
2. **Larger RDS**: db.t4g.small ($30/month)
3. **Add ALB**: For high availability ($20/month)
4. **Add auto-scaling**: Multiple EC2 instances
5. **Add CloudFront**: CDN for frontend

## Cleanup

To tear down everything:

```bash
cd infra/terraform
terraform destroy -var-file="personal.tfvars"
```

⚠️ **Warning:** This deletes everything including the database!

## Next Steps

1. ✅ Set up automated backups
2. ✅ Configure CloudWatch alarms
3. ✅ Set up log aggregation
4. ✅ Add monitoring dashboard
5. ✅ Create runbooks
6. ✅ Set up CI/CD (GitHub Actions)

## CI/CD with GitHub Actions

The included workflow can be adapted for EC2:
- Build images
- SCP images to EC2
- SSH and deploy

See `.github/workflows/deploy.yml` for details.

## Support

Common issues:
1. Check container logs: `docker-compose logs`
2. Check Nginx config: `docker exec species-nginx nginx -t`
3. Check SSL certificates: `docker-compose run --rm certbot certificates`
4. Check database connection: `docker exec species-backend python manage.py check --database default`

For persistent issues:
- Review CloudWatch logs
- Check security group rules
- Verify DNS propagation
- Check disk space
