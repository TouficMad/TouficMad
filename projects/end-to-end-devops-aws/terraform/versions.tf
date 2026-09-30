terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment once you have a state bucket
  # backend "s3" {
  #   bucket  = "CHANGE-ME-tfstate"
  #   key     = "end-to-end-devops-aws/terraform.tfstate"
  #   region  = "eu-west-1"
  #   encrypt = true
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = var.name
      ManagedBy = "terraform"
    }
  }
}
