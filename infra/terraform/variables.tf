# infra/terraform/variables.tf
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-3"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro" # 7$/month
}

variable "volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 30
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # freetier
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
}

variable "ssh_allowed_ips" {
  description = "IP addresses allowed to SSH (CIDR notation)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # IMPORTANT: Restrict this in production!
}

variable "ssh_allowed_ipv6" {
  description = "IPv6 addresses allowed to SSH (CIDR notation)"
  type        = list(string)
  default     = []
}
variable "resend_api_key" {
  description = "Resend API key for email"
  type        = string
  sensitive   = true
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance. Pin this to a specific value to prevent Terraform from replacing the instance when a new Ubuntu AMI is published. Get the current value with: aws ec2 describe-instances --instance-ids <id> --query 'Reservations[0].Instances[0].ImageId' --output text"
  type        = string
}
