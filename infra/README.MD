# Marine Species Tracker — Infrastructure

Simple, cost-effective infrastructure for the Marine Species Tracker application.

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│ Route53 DNS                                 │
│  - species.kuroshio-lab.com                 │
│  - api.species.kuroshio-lab.com             │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ EC2 Instance (t3.micro)                     │
│ ┌─────────────────────────────────────────┐ │
│ │ Nginx (HTTPS with Let's Encrypt)        │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Backend (Django in Docker)              │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Frontend (Next.js in Docker)            │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Database (PostgreSQL + PostGIS Docker)  │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

The database runs as a Docker container on the EC2 instance, with data persisted via Docker volumes on EBS. There is no managed RDS instance.

---

## Cost Breakdown

**Monthly Cost: ~$15**

| Resource | Type | Cost/Month |
|---|---|---|
| EC2 | t3.micro | ~$8 |
| Public IP | IPv4 Fee | ~$3.60 |
| EBS | 30GB gp3 | ~$3 |
| Route53 | DNS + queries | ~$1 |
| Data Transfer | Minimal | ~$1 |
| **Total** | | **~$17** |

**vs. ECS + ALB setup: ~$93/month — 80% cheaper**

---

## Structure

```
infra/
├── terraform/
│   ├── backend.tf              # S3 remote state config
│   ├── main.tf                 # EC2 + networking + IAM + secrets
│   ├── user-data.sh            # EC2 initialization script
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Terraform outputs
│   ├── personal.tfvars.example # Example config
│   └── personal.tfvars         # Your config (gitignored)
├── scripts/
│   ├── deploy.sh               # Deploy application to EC2
│   └── migrate.sh              # Run Django migrations on EC2
└── docs/
    └── DEPLOYMENT.MD           # Detailed deployment guide
```

---

## Quick Deploy

### 1. Generate SSH Key

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/species-tracker
```

### 2. Configure Variables

```bash
cd infra/terraform
cp personal.tfvars.example personal.tfvars
# Edit personal.tfvars with your values
```

Required fields in `personal.tfvars`:

| Variable | Description |
|---|---|
| `ssh_public_key` | Contents of `~/.ssh/species-tracker.pub` |
| `resend_api_key` | Your Resend API key for email |
| `ami_id` | AMI ID to use for the EC2 instance |
| `ssh_allowed_ips` | CIDR list for SSH access (restrict in production!) |

**First deploy** — look up the latest Ubuntu 22.04 AMI for `eu-west-3`:
```bash
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
            "Name=virtualization-type,Values=hvm" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text
```

**Existing instance** — always pin to the AMI already running to avoid replacement:
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=species-tracker-app" \
  --query 'Reservations[0].Instances[0].ImageId' \
  --output text
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

# SSH into EC2
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP

# 1. Start temporary bootstrap Nginx on port 80
sudo docker run --rm -d \
  --name nginx-bootstrap \
  -v species-tracker_certbot-www:/var/www/certbot \
  -p 80:80 \
  nginx:alpine \
  sh -c "echo 'events {} http { server { listen 80; server_name species.kuroshio-lab.com api.species.kuroshio-lab.com; location /.well-known/acme-challenge/ { root /var/www/certbot; } } }' > /etc/nginx/nginx.conf && nginx -g \"daemon off;\""

# 2. Run Certbot to request the certificate
cd /opt/species-tracker
sudo docker-compose run --rm --no-deps --entrypoint "certbot" certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@kuroshio-lab.com \
    --agree-tos \
    --no-eff-email \
    -d species.kuroshio-lab.com \
    -d api.species.kuroshio-lab.com

# 3. Stop the bootstrap container
sudo docker stop nginx-bootstrap
```

### 5. Deploy Application

```bash
cd ../scripts
chmod +x deploy.sh migrate.sh
./deploy.sh
./migrate.sh
```

### 6. Visit Your App

- Frontend: https://species.kuroshio-lab.com
- API: https://api.species.kuroshio-lab.com
- Admin: https://api.species.kuroshio-lab.com/admin/

---

## What Gets Created

### Networking
- VPC (10.0.0.0/16)
- 2 public subnets across 2 AZs
- Internet Gateway
- No NAT Gateway (cost savings)

### Compute
- EC2 t3.micro instance (configurable via `instance_type`)
- AMI pinned via `ami_id` variable to prevent accidental replacement
- `user_data_replace_on_change = false` — user data changes never trigger instance replacement
- Docker + Docker Compose pre-installed via `user-data.sh`
- Nginx with Let's Encrypt SSL
- Elastic IP (stable public IP)

### Database (Docker on EC2)
- PostgreSQL 14 with PostGIS (Docker container on the EC2 instance)
- Data persisted via Docker volumes on EBS
- Manual backups via `pg_dump` (see Backup section)

### IAM
- EC2 instance role with policies for:
  - **SSM** — AWS Systems Manager access
  - **S3** — media upload/download access
  - **SES** — sending emails
  - **Route53** — DNS record updates
  - **Secrets Manager** — reading DB password, Django secret key, Resend API key

### Secrets (AWS Secrets Manager)
- `species-tracker-db-password-*` — PostgreSQL password (auto-generated)
- `species-tracker-django-secret-*` — Django `SECRET_KEY` (auto-generated)
- `species-tracker-resend-api-*` — Resend API key (from `personal.tfvars`)

### Security
- EC2 security group (SSH, HTTP, HTTPS)
- Let's Encrypt SSL certificates (auto-renewed every 12 hours)

### DNS
- Route53 records:
  - `species.kuroshio-lab.com` → Frontend
  - `api.species.kuroshio-lab.com` → Backend API

### Monitoring
- CloudWatch Log Group: `/species-tracker/app` (7-day retention)
- SNS topic: `species-tracker-alarms`
- CloudWatch Alarms:
  - EC2 CPU > 80%

---

## Common Operations

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

> **Note:** Changing `instance_type` causes downtime as the instance must be stopped and restarted. Keep `ami_id` set to the currently running AMI to avoid triggering a full replacement (data loss).

### Sync Terraform State with AWS

If the Terraform state has drifted from reality (e.g. after manual changes or a previous failed apply):

```bash
terraform apply -refresh-only -var-file="personal.tfvars"
```

### Update Infrastructure

```bash
cd infra/terraform
terraform apply -var-file="personal.tfvars"
```

---

## Security

### SSH Access
- Key-based authentication only
- Restrict SSH to specific IPs via `ssh_allowed_ips` in `personal.tfvars`
- Default allows from anywhere (change for production!)

### Application Security
- HTTPS enforced via Nginx
- Let's Encrypt SSL certificates (auto-renewed)
- Security headers configured
- Rate limiting enabled
- CORS properly configured

### Database Security
- Not exposed outside the Docker network
- Only accessible from within the EC2 instance
- Password stored in AWS Secrets Manager

### Secrets
- Stored in AWS Secrets Manager
- Never in git or environment files
- Automatically injected into containers at startup

---

## Monitoring

### CloudWatch Alarms
- EC2 CPU > 80% → SNS topic `species-tracker-alarms`

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

---

## SSL Certificate Management

Certificates auto-renew via certbot container every 12 hours.

Manual renewal:
```bash
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP
cd /opt/species-tracker
docker-compose run --rm certbot renew
docker-compose restart nginx
```

---

## Backup & Recovery

### Database Backups

The database runs in Docker — there are no automated RDS backups. Take manual backups with:

```bash
docker exec species-db pg_dump -U postgres marine_tracker > backup.sql
```

### Application Files
- Docker volumes persist data on EBS (encrypted, 30GB gp3)
- Data survives container restarts and redeployments

---

## Scaling Options

### Current Setup (~$17/month)
- Single EC2 t3.micro
- Docker-based PostgreSQL on EBS
- Single point of failure

### Medium Scale (~$80/month)
- Upgrade to t3.medium EC2 (~$30)
- Migrate DB to RDS db.t4g.small (~$30)
- Add CloudFront CDN (~$20)

### Production Scale (~$150/month)
- Application Load Balancer (~$20)
- Multiple EC2 instances behind ALB
- Larger RDS instance
- Auto-scaling group
- Multi-AZ RDS deployment

---

## Troubleshooting

### `terraform plan` Shows Instance Replacement

If the plan shows `aws_instance.app must be replaced` due to an AMI change, your `ami_id` in `personal.tfvars` doesn't match what's running. Fix it:

```bash
# Get the real AMI from AWS
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=species-tracker-app" \
  --query 'Reservations[0].Instances[0].ImageId' \
  --output text

# Update personal.tfvars with that value, then sync state
terraform apply -refresh-only -var-file="personal.tfvars"
```

### Services Won't Start

```bash
ssh -i ~/.ssh/species-tracker ubuntu@$EC2_IP
cd /opt/species-tracker
docker-compose logs
```

Common causes: missing environment variables, database connection failure, out of memory, port conflicts.

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
# Check if database container is running
docker ps | grep species-db

# Check database logs
docker-compose logs db
```

### Out of Disk Space

```bash
# Check usage
df -h
docker system df

# Clean up
docker system prune -a --volumes
```

---

## Cleanup

To destroy all AWS resources:

```bash
cd infra/terraform
terraform destroy -var-file="personal.tfvars"
```

> **Warning:** This deletes all data including the database!

---

## Documentation

- [Detailed Deployment Guide](docs/DEPLOYMENT.MD)

---

## Related

- [Backend README](../backend/README.md)
- [Frontend README](../frontend/README.MD)
- [Docker Compose](../docker-compose.yml)

---

## Tips

1. **SSH Config** — add to `~/.ssh/config` for convenient access:
   ```
   Host species-tracker
     HostName [EC2_IP]
     User ubuntu
     IdentityFile ~/.ssh/species-tracker
   ```

2. **Deploy alias** — add to `~/.bashrc`:
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

## Future Enhancements

- [ ] Add CloudFront CDN
- [ ] Implement auto-scaling
- [ ] Add Redis for caching
- [ ] Implement CI/CD with GitHub Actions
- [ ] Add monitoring dashboard
- [ ] Set up log aggregation
- [ ] Implement blue-green deployments
