# infra/terraform/main.tf
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Kuroshio-Lab"
      Application = "marine-species-tracker"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# =============================================================================
# Reference Global Infrastructure (from your infra repo)
# =============================================================================

data "terraform_remote_state" "global" {
  backend = "s3"
  config = {
    bucket = "kuroshio-lab-terraform-state"
    key    = "shared/terraform.tfstate"
    region = var.aws_region
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# =============================================================================
# VPC and Networking (Simplified - no NAT Gateway)
# =============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "species-tracker-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "species-tracker-igw"
  }
}

# Public Subnets (for EC2 and RDS)
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "species-tracker-public-${count.index + 1}"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "species-tracker-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# =============================================================================
# Security Groups
# =============================================================================

resource "aws_security_group" "ec2" {
  name_prefix = "species-tracker-ec2-"
  description = "Security group for EC2 instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_ips
    description = "SSH access (IPv4)"
  }

  # SSH access (IPv6)
  ingress {
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    ipv6_cidr_blocks = var.ssh_allowed_ipv6
    description      = "SSH access (IPv6)"
  }

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "species-tracker-ec2-sg"
  }
}

# =============================================================================
# RDS PostgreSQL with PostGIS
# =============================================================================

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "db_password" {
  name_prefix             = "species-tracker-db-password-"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# =============================================================================
# EC2 Instance
# =============================================================================

# AMI is pinned via var.ami_id to prevent accidental EC2 instance replacement.
# To find the current instance's AMI:
#   aws ec2 describe-instances --instance-ids <id> \
#     --query 'Reservations[0].Instances[0].ImageId' --output text

# Key pair for SSH access
resource "aws_key_pair" "deployer" {
  key_name   = "species-tracker-deployer"
  public_key = var.ssh_public_key

  tags = {
    Name = "species-tracker-deployer"
  }
}

# IAM role for EC2
resource "aws_iam_role" "ec2" {
  name = "species-tracker-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "species-tracker-ec2-role"
  }
}

resource "aws_iam_role_policy_attachment" "ssm_managed" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ec2_route53" {
  name = "route53-record-update-access"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "route53:ChangeResourceRecordSets",
        "route53:ListResourceRecordSets"
      ]
      Resource = [
        "arn:aws:route53:::hostedzone/${data.terraform_remote_state.global.outputs.hosted_zone_id}"
      ]
    }]
  })
}

# S3 access for media uploads
resource "aws_iam_role_policy" "ec2_s3" {
  name = "s3-access"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      Resource = [
        "arn:aws:s3:::${data.terraform_remote_state.global.outputs.s3_bucket_name}",
        "arn:aws:s3:::${data.terraform_remote_state.global.outputs.s3_bucket_name}/species/*"
      ]
    }]
  })
}

# SES access for emails
resource "aws_iam_role_policy" "ec2_ses" {
  name = "ses-access"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ]
      Resource = "*"
    }]
  })
}

# Secrets Manager access
resource "aws_iam_role_policy" "ec2_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.db_password.arn,
        aws_secretsmanager_secret.django_secret.arn,
        aws_secretsmanager_secret.resend_api.arn
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "species-tracker-ec2-profile"
  role = aws_iam_role.ec2.name
}

# Application Secrets
resource "random_password" "django_secret" {
  length  = 50
  special = true
}

resource "aws_secretsmanager_secret" "django_secret" {
  name_prefix             = "species-tracker-django-secret-"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "django_secret" {
  secret_id     = aws_secretsmanager_secret.django_secret.id
  secret_string = random_password.django_secret.result
}

resource "aws_secretsmanager_secret" "resend_api" {
  name_prefix             = "species-tracker-resend-api-"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "resend_api" {
  secret_id     = aws_secretsmanager_secret.resend_api.id
  secret_string = var.resend_api_key
}


# EC2 Instance
resource "aws_instance" "app" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  # User data script for EC2 initialization
  user_data_base64 = base64gzip(templatefile("${path.module}/user-data.sh", {
    db_host                = "db"
    db_name                = "marine_tracker"
    db_user                = "postgres"
    db_password_secret_arn = aws_secretsmanager_secret.db_password.arn
    django_secret_arn      = aws_secretsmanager_secret.django_secret.arn
    resend_api_secret_arn  = aws_secretsmanager_secret.resend_api.arn
    s3_bucket_name         = data.terraform_remote_state.global.outputs.s3_bucket_name
    aws_region             = var.aws_region
    frontend_domain        = "species.kuroshio-lab.com"
    api_domain             = "api.species.kuroshio-lab.com"
    environment            = var.environment
    logging_level          = var.environment == "production" ? "ERROR" : "INFO"
    hosted_zone_id         = data.terraform_remote_state.global.outputs.hosted_zone_id

  }))

  user_data_replace_on_change = false

  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "species-tracker-app"
  }

}

# Elastic IP for stable public IP
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name = "species-tracker-eip"
  }
}

# =============================================================================
# CloudWatch Logs
# =============================================================================

resource "aws_cloudwatch_log_group" "app" {
  name              = "/species-tracker/app"
  retention_in_days = 7

  tags = {
    Name = "species-tracker-app-logs"
  }
}

# =============================================================================
# SNS Topic for Alarms (Managed locally for this project)
# =============================================================================

resource "aws_sns_topic" "alarms" {
  name = "species-tracker-alarms"
}

# =============================================================================
# CloudWatch Alarms
# =============================================================================


resource "aws_cloudwatch_metric_alarm" "ec2_cpu" {
  alarm_name          = "species-tracker-ec2-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when EC2 CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.alarms.arn] // Changed from data.terraform_remote_state.global.outputs.sns_alarms_topic_arn

  dimensions = {
    InstanceId = aws_instance.app.id
  }
}
