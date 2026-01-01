#!/bin/bash
# infra/terraform/user-data.sh
# EC2 initialization script

set -e

# =============================================================================
# Update system
# =============================================================================
apt-get update
apt-get upgrade -y

# =============================================================================
# Install dependencies
# =============================================================================
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    jq \
    awscli

# =============================================================================
# Install Docker
# =============================================================================
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# =============================================================================
# Install Docker Compose (standalone)
# =============================================================================
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# =============================================================================
# Create application directory
# =============================================================================
mkdir -p /opt/species-tracker
cd /opt/species-tracker

# =============================================================================
# Update Route53 DNS Records
# =============================================================================
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# HOSTED_ZONE_ID will be passed as a template variable from main.tf
# Update frontend DNS record
aws route53 change-resource-record-sets \
  --hosted-zone-id "${hosted_zone_id}" \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "${frontend_domain}",
          "Type": "A",
          "TTL": 300,
          "ResourceRecords": [
            { "Value": "'"$EC2_PUBLIC_IP"'" }
          ]
        }
      }
    ]
  }'

  # Update API DNS record
aws route53 change-resource-record-sets \
  --hosted-zone-id "${hosted_zone_id}" \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "${api_domain}",
          "Type": "A",
          "TTL": 300,
          "ResourceRecords": [
            { "Value": "'"$EC2_PUBLIC_IP"'" }
          ]
        }
      }
    ]
  }'
# =============================================================================
# Fetch secrets from AWS Secrets Manager
# =============================================================================
DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id ${db_password_secret_arn} --region ${aws_region} --query SecretString --output text)
DJANGO_SECRET=$(aws secretsmanager get-secret-value --secret-id ${django_secret_arn} --region ${aws_region} --query SecretString --output text)
RESEND_API=$(aws secretsmanager get-secret-value --secret-id ${resend_api_secret_arn} --region ${aws_region} --query SecretString --output text)

# =============================================================================
# Create environment file
# =============================================================================
cat > .env << EOF
# Database
DB_HOST=${db_host}
DB_NAME=${db_name}
DB_USER=${db_user}
DB_PASSWORD=$DB_PASSWORD
DB_PORT=5432

# Django
DJANGO_SECRET_KEY=$DJANGO_SECRET
DEBUG=False
ENV=${environment}
LOGGING_LEVEL=${logging_level}
ALLOWED_HOSTS=${api_domain},localhost,backend,species-backend
CORS_ALLOWED_ORIGINS=https://${frontend_domain}
CSRF_TRUSTED_ORIGINS=https://${frontend_domain}
AUTH_COOKIE_DOMAIN=.kuroshio-lab.com

# AWS
USE_S3=True
AWS_STORAGE_BUCKET_NAME=${s3_bucket_name}
AWS_S3_REGION_NAME=${aws_region}

# Email
RESEND_API=$RESEND_API
DEFAULT_FROM_EMAIL=Kuroshio Lab <no-reply@notifications.kuroshio-lab.com>

# Frontend
NEXT_PUBLIC_API_URL=https://${api_domain}
INTERNAL_API_URL=http://backend:8000
NODE_ENV=production

# Domains (for Nginx)
FRONTEND_DOMAIN=${frontend_domain}
API_DOMAIN=${api_domain}
EOF

# =============================================================================
# Create docker-compose.yml
# =============================================================================
cat > docker-compose.yml << 'DOCKERCOMPOSE'
version: '3.8'

services:
  backend:
    image: backend:latest
    container_name: species-backend
    restart: unless-stopped
    env_file: .env
    expose:
      - "8000"
    volumes:
      - backend-static:/app/staticfiles
      - backend-media:/app/media
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    image: frontend:latest
    container_name: species-frontend
    restart: unless-stopped
    env_file: .env
    expose:
      - "3000"
    networks:
      - app-network
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    container_name: species-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - backend-static:/var/www/static:ro
      - backend-media:/var/www/media:ro
      - certbot-conf:/etc/letsencrypt:ro
      - certbot-www:/var/www/certbot:ro
    networks:
      - app-network
    depends_on:
      - backend
      - frontend

  certbot:
    image: certbot/certbot
    container_name: species-certbot
    volumes:
      - certbot-conf:/etc/letsencrypt
      - certbot-www:/var/www/certbot
    command: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $$$$!; done;'"
volumes:
  backend-static:
  backend-media:
  certbot-conf:
  certbot-www:

networks:
  app-network:
    driver: bridge
DOCKERCOMPOSE

# =============================================================================
# Create Nginx configuration
# =============================================================================
cat > nginx.conf << NGINXCONF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=general_limit:10m rate=50r/s;

    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # HTTP redirect to HTTPS
    server {
        listen 80;
        server_name ${frontend_domain} ${api_domain};

        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect everything else to HTTPS
        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    # Frontend (species.kuroshio-lab.com)
    server {
        listen 443 ssl http2;
        server_name ${frontend_domain};

        ssl_certificate /etc/letsencrypt/live/${frontend_domain}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/${frontend_domain}/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        location / {
            limit_req zone=general_limit burst=20 nodelay;
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_cache_bypass \$http_upgrade;
        }
    }

    # API (api.species.kuroshio-lab.com)
    server {
        listen 443 ssl http2;
        server_name ${api_domain};

        ssl_certificate /etc/letsencrypt/live/${frontend_domain}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/${frontend_domain}/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        # Django static files
        location /static/ {
            alias /var/www/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /var/www/media/;
            expires 7d;
            add_header Cache-Control "public";
        }

        # API endpoints
        location / {
            limit_req zone=api_limit burst=5 nodelay;
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
NGINXCONF

# =============================================================================
# Create deployment script
# =============================================================================
cat > deploy.sh << 'DEPLOYSCRIPT'
#!/bin/bash
set -e

echo "🚀 Deploying Species Tracker..."

# Stop existing containers
docker-compose down || true

# Pull latest images (will be pushed from CI/CD or manual deploy)
docker-compose pull || echo "No images to pull yet"

# Start containers
docker-compose up -d

# Wait for backend to be healthy
echo "⏳ Waiting for backend to be healthy..."
for i in {1..30}; do
    if docker exec species-backend curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "✅ Deployment complete!"
DEPLOYSCRIPT

chmod +x deploy.sh

# =============================================================================
# Create SSL certificate setup script
# =============================================================================
cat > setup-ssl.sh << SSLSCRIPT
#!/bin/bash
set -e

echo "🔐 Setting up SSL certificates..."

# Start nginx with temporary config for Let's Encrypt challenge
docker-compose up -d --no-deps nginx

# Wait for nginx to start
sleep 5

# Get SSL certificates
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@kuroshio-lab.com \
    --agree-tos \
    --no-eff-email \
    -d ${frontend_domain} \
    -d ${api_domain}

# Restart nginx with SSL
docker-compose restart nginx

echo "✅ SSL certificates installed!"
SSLSCRIPT

chmod +x setup-ssl.sh

# =============================================================================
# Create log rotation configuration
# =============================================================================
cat > /etc/logrotate.d/docker-containers << 'LOGROTATE'
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    size 10M
    missingok
    delaycompress
    copytruncate
}
LOGROTATE

# =============================================================================
# Create CloudWatch agent configuration (optional)
# =============================================================================
mkdir -p /opt/aws/amazon-cloudwatch-agent/etc/
cat > /opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json << 'CWCONFIG'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/lib/docker/containers/*/*.log",
            "log_group_name": "/species-tracker/app",
            "log_stream_name": "{instance_id}/docker"
          }
        ]
      }
    }
  }
}
CWCONFIG

# =============================================================================
# Setup complete message
# =============================================================================
cat > /root/SETUP_COMPLETE << 'SETUPMSG'
Species Tracker EC2 Setup Complete!

To deploy the application:
1. SSH into this instance
2. cd /opt/species-tracker
3. Push Docker images from your local machine or CI/CD
4. Run: ./setup-ssl.sh (first time only)
5. Run: ./deploy.sh

Docker Compose commands:
- View logs: docker-compose logs -f
- Restart: docker-compose restart
- Stop: docker-compose down
- Start: docker-compose up -d

Application URLs:
- Frontend: https://${frontend_domain}
- API: https://${api_domain}

Database connection configured automatically.
All secrets are fetched from AWS Secrets Manager.
SETUPMSG

echo "✅ EC2 setup complete! See /root/SETUP_COMPLETE for details."
