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

  # SSH access (restrict to your IP in production)
  # SSH access (IPv4)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_ips
    description = "SSH access (IPv4)"
  }

  # SSH access (IPv6) - ADD THIS
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

resource "aws_security_group" "rds" {
  name_prefix = "species-tracker-rds-"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
    description     = "PostgreSQL from EC2"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "species-tracker-rds-sg"
  }
}

# =============================================================================
# RDS PostgreSQL with PostGIS
# =============================================================================

resource "aws_db_subnet_group" "main" {
  name       = "species-tracker-db-subnet-group"
  subnet_ids = aws_subnet.public[*].id

  tags = {
    Name = "species-tracker-db-subnet-group"
  }
}

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

resource "aws_db_instance" "main" {
  identifier        = "species-tracker-postgres"
  engine            = "postgres"
  engine_version    = "14.17"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "marine_tracker"
  username = "postgres"
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "species-tracker-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Name = "species-tracker-postgres"
  }
}

# =============================================================================
# EC2 Instance
# =============================================================================

# Get latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

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
        "route53:ListResourceRecordSets" # Often useful for debugging/checking
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
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  # User data script for EC2 initialization
  user_data = templatefile("${path.module}/user-data.sh", {
    db_host                = aws_db_instance.main.address
    db_name                = aws_db_instance.main.db_name
    db_user                = aws_db_instance.main.username
    db_password_secret_arn = aws_secretsmanager_secret.db_password.arn
    django_secret_arn      = aws_secretsmanager_secret.django_secret.arn
    resend_api_secret_arn  = aws_secretsmanager_secret.resend_api.arn
    s3_bucket_name         = data.terraform_remote_state.global.outputs.s3_bucket_name
    aws_region             = var.aws_region
    frontend_domain        = "species.kuroshio-lab.com"
    api_domain             = "api.species.kuroshio-lab.com"
    environment            = var.environment
    hosted_zone_id         = data.terraform_remote_state.global.outputs.hosted_zone_id

  })

  user_data_replace_on_change = true
  
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

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "species-tracker-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when RDS CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.alarms.arn] // Changed from data.terraform_remote_state.global.outputs.sns_alarms_topic_arn

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "species-tracker-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "2000000000" # 2GB in bytes
  alarm_description   = "Alert when RDS storage < 2GB"
  alarm_actions       = [aws_sns_topic.alarms.arn] // Changed from data.terraform_remote_state.global.outputs.sns_alarms_topic_arn

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}
