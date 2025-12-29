# Marine Species Tracker - Infrastructure

Simple, cost-effective infrastructure for the Marine Species Tracker application.

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────┐
│ Route53 DNS                                 │
│  - species.kuroshio-lab.com                 │
│  - api.species.kuroshio-lab.com             │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ EC2 Instance (t3.small)                     │
│ ┌─────────────────────────────────────────┐ │
│ │ Nginx (HTTPS with Let's Encrypt)        │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Backend (Django in Docker)              │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Frontend (Next.js in Docker)            │ │
│ └─────────────────────────────────────────┘ │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ RDS PostgreSQL (db.t4g.micro)               │
│  - PostGIS enabled                          │
│  - 20GB storage                             │
│  - 7-day automated backups                  │
└─────────────────────────────────────────────┘
```

## 💰 Cost Breakdown

**Monthly Cost: ~$35**

| Resource | Type | Cost/Month |
|----------|------|------------|
| EC2 | t3.small (2 vCPU, 2GB RAM) | ~$15 |
| RDS | db.t4g.micro (PostgreSQL) | ~$15 |
| EBS | 30GB gp3 | ~$3 |
| Route53 | DNS + queries | ~$1 |
| Data Transfer | Minimal | ~$1 |
| **Total** | | **~$35** |

**vs. ECS + ALB setup: ~$93/month**
**Savings: $58/month (62% cheaper!)**

## 📁 Structure

```
infra/
├── terraform/
│   ├── backend.tf              # S3 backend config
│   ├── main.tf                 # EC2 + RDS infrastructure
│   ├── user-data.sh            # EC2 initialization script
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Terraform outputs
│   ├── personal.tfvars.example # Example config
│   └── personal.tfvars         # Your config (gitignored)
├── scripts/
│   ├── deploy.sh               # Deploy to EC2
│   └── migrate.sh              # Run migrations
└── docs/
    └── DEPLOYMENT.md           # Detailed guide
```

## 🚀 Quick Deploy

### 1. Generate SSH Key

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/species-tracker
```

### 2. Configure Variables

```bash
cd infra/terraform
cp personal.tfvars.example personal.tfvars
# Edit personal.tfvars with your SSH public key and Resend API key
```

### 3. Deploy Infrastructure

```bash
terraform init
terraform apply -var-file="personal.tfvars"
```

### 4. Setup SSL Certificates

```bash
# Get EC2 IP
EC2_IP=$(terraform output -raw instance_public_ip)

# SSH and setup SSL
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP
cd /opt/species-tracker
sudo ./setup-ssl.sh
exit
```

### 5. Deploy Application

```bash
cd ../scripts
./deploy.sh
./migrate.sh
```

### 6. Visit Your App

- Frontend: https://species.kuroshio-lab.com
- API: https://api.species.kuroshio-lab.com
- Admin: https://api.species.kuroshio-lab.com/admin/

## 📦 What Gets Created

### Networking
- VPC (10.0.0.0/16)
- 2 public subnets across 2 AZs
- Internet Gateway
- No NAT Gateway (cost savings!)

### Compute
- EC2 t3.small instance
- Docker + Docker Compose pre-installed
- Nginx with Let's Encrypt SSL
- Elastic IP (static IP address)
- IAM role for S3 and SES access

### Database
- RDS PostgreSQL 14 with PostGIS
- db.t4g.micro instance
- 20GB gp3 storage
- 7-day automated backups
- Daily maintenance window

### Security
- Security groups (EC2, RDS)
- IAM role and policies
- Secrets Manager for credentials
- Let's Encrypt SSL certificates

### DNS
- Route53 records for:
  - species.kuroshio-lab.com
  - api.species.kuroshio-lab.com

### Monitoring
- CloudWatch alarms (CPU, RDS)
- CloudWatch Logs integration
- Container health checks

## 🔧 Common Operations

### Deploy Code Changes

```bash
cd infra/scripts
./deploy.sh
```

### View Logs

```bash
ssh -i ~/.ssh/species-tracker ubuntu@$(cd infra/terraform && terraform output -raw instance_public_ip)
cd /opt/species-tracker
docker-compose logs -f
```

### Restart Services

```bash
ssh -i ~/.ssh/species-tracker ubuntu@$(cd infra/terraform && terraform output -raw instance_public_ip)
cd /opt/species-tracker
docker-compose restart
```

### Run Django Commands

```bash
ssh -i ~/.ssh/species-tracker ubuntu@$(cd infra/terraform && terraform output -raw instance_public_ip)
cd /opt/species-tracker
docker exec -it species-backend python manage.py [command]
```

### Scale Instance Size

Edit `personal.tfvars`:
```hcl
instance_type = "t3.medium"  # Upgrade to 2 vCPU, 4GB RAM
```

Apply:
```bash
terraform apply -var-file="personal.tfvars"
```

**Note:** This causes downtime as the instance is replaced.

### Update Infrastructure

```bash
cd infra/terraform
terraform apply -var-file="personal.tfvars"
```

## 🔐 Security

### SSH Access
- Key-based authentication only
- Restrict SSH to specific IPs via `ssh_allowed_ips`
- Default allows from anywhere (⚠️ change for production!)

### Application Security
- HTTPS enforced via Nginx
- Let's Encrypt SSL certificates (auto-renewed)
- Security headers configured
- Rate limiting enabled
- CORS properly configured

### Database Security
- Not publicly accessible
- Only accessible from EC2 instance
- Encrypted at rest
- Encrypted in transit

### Secrets
- Stored in AWS Secrets Manager
- Never in git or environment files
- Automatically injected into containers

## 📊 Monitoring

### CloudWatch Alarms
- EC2 CPU > 80%
- RDS CPU > 80%
- RDS storage < 2GB

All alarms send to SNS topic (configured in global infra).

### Logs
- Container logs: `/var/lib/docker/containers/*/*.log`
- Nginx logs: Inside nginx container
- Application logs: Via Docker Compose

View logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

## 🔄 SSL Certificate Management

Certificates auto-renew via certbot container every 12 hours.

Manual renewal:
```bash
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP
cd /opt/species-tracker
docker-compose run --rm certbot renew
docker-compose restart nginx
```

## 💾 Backup & Recovery

### Database Backups
- RDS automated backups: 7-day retention
- Backup window: 03:00-04:00 UTC
- Point-in-time recovery enabled

### Manual Backup
```bash
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP
docker exec species-backend python manage.py dumpdata > backup.json
```

### Application Files
- Docker volumes persist data
- Stored on EBS (encrypted)
- Survives container restarts

## 📈 Scaling Options

### Current Setup (Dev/Small)
- **Cost:** ~$35/month
- **Capacity:** Small traffic
- **Single point of failure**

### Medium Scale (~$80/month)
- Upgrade to t3.medium EC2 (~$30)
- Upgrade to db.t4g.small RDS (~$30)
- Add CloudFront CDN (~$20)

### Production Scale (~$150/month)
- Add Application Load Balancer (~$20)
- Multiple EC2 instances behind ALB
- Larger RDS instance
- Auto-scaling group
- Multi-AZ RDS deployment

## 🚨 Troubleshooting

### Services Won't Start

```bash
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP
cd /opt/species-tracker
docker-compose logs
```

Common issues:
- Environment variables not set
- Database connection failed
- Out of memory
- Port conflicts

### SSL Certificate Issues

```bash
# Check certificates
docker-compose run --rm certbot certificates

# Manually renew
docker-compose run --rm certbot renew
docker-compose restart nginx
```

### Database Connection Failed

```bash
# Test connection
docker exec species-backend python manage.py check --database default

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier species-tracker-postgres
```

### Out of Disk Space

```bash
# Check usage
df -h
docker system df

# Clean up
docker system prune -a --volumes
```

## 🗑️ Cleanup

To destroy everything:

```bash
cd infra/terraform
terraform destroy -var-file="personal.tfvars"
```

⚠️ **Warning:** This deletes all data including the database!

## 📚 Documentation

- [Detailed Deployment Guide](docs/DEPLOYMENT.md)
- [Docker Compose Setup](#) (auto-configured on EC2)
- [Nginx Configuration](#) (auto-configured on EC2)
- [Global Infrastructure](https://github.com/your-org/infra)

## 🔗 Related

- Backend: [../backend/README.md](../backend/README.md)
- Frontend: [../frontend/README.md](../frontend/README.md)
- Docker Compose: [../docker-compose.yml](../docker-compose.yml)

## 💡 Tips

1. **SSH Config:** Add to `~/.ssh/config`:
   ```
   Host species-tracker
     HostName [EC2_IP]
     User ubuntu
     IdentityFile ~/.ssh/species-tracker
   ```

2. **Alias for deploy:** Add to `~/.bashrc`:
   ```bash
   alias deploy-species="cd /path/to/repo/infra/scripts && ./deploy.sh"
   ```

3. **Monitor costs:**
   ```bash
   aws ce get-cost-and-usage \
     --time-period Start=$(date -d '1 month ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
     --granularity MONTHLY \
     --metrics BlendedCost
   ```

## 📞 Support

For issues:
1. Check Docker logs: `docker-compose logs`
2. Check Nginx: `docker exec species-nginx nginx -t`
3. Check SSL: `docker-compose run --rm certbot certificates`
4. Check database: `docker exec species-backend python manage.py check --database default`
5. Check CloudWatch alarms in AWS Console

## 🎯 Future Enhancements

- [ ] Add CloudFront CDN
- [ ] Implement auto-scaling
- [ ] Add Redis for caching
- [ ] Implement CI/CD with GitHub Actions
- [ ] Add monitoring dashboard
- [ ] Set up log aggregation
- [ ] Implement blue-green deployments
