# infra/terraform/backend.tf
terraform {
  required_version = ">= 1.0"

  backend "s3" {
    bucket         = "kuroshio-lab-terraform-state"
    key            = "marine-species-tracker/terraform.tfstate"
    region         = "eu-west-3"
    encrypt        = true
    dynamodb_table = "kuroshio-lab-terraform-locks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
