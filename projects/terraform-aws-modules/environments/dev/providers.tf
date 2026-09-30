terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment after creating the state bucket (see README "Remote state")
  # backend "s3" {
  #   bucket       = "CHANGE-ME-tfstate"
  #   key          = "dev/terraform.tfstate"
  #   region       = "eu-west-1"
  #   use_lockfile = true # native S3 locking, Terraform >= 1.10
  #   encrypt      = true
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Repository = "terraform-aws-modules"
    }
  }
}
