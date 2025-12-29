# infra/terraform/outputs.tf
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "instance_public_ip" {
  description = "EC2 instance public IP (Elastic IP)"
  value       = aws_eip.app.public_ip
}

output "instance_public_dns" {
  description = "EC2 instance public DNS"
  value       = aws_instance.app.public_dns
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "https://species.kuroshio-lab.com"
}

output "api_url" {
  description = "API URL"
  value       = "https://api.species.kuroshio-lab.com"
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/species-tracker ubuntu@${aws_eip.app.public_ip}"
}

output "db_password_secret_arn" {
  description = "ARN of the database password secret"
  value       = aws_secretsmanager_secret.db_password.arn
  sensitive   = true
}

output "sns_alarms_topic_arn" {
  description = "The ARN of the SNS topic for alarms"
  value       = aws_sns_topic.alarms.arn
}
