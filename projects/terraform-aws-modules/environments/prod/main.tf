locals {
  name = "${var.project}-prod"
  tags = {
    Project     = var.project
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

data "aws_caller_identity" "current" {}

module "vpc" {
  source = "../../modules/vpc"

  name               = local.name
  cidr_block         = "10.20.0.0/16"
  az_count           = 2
  enable_nat_gateway = true
  tags               = local.tags
}

module "artifacts_bucket" {
  source = "../../modules/s3"

  bucket_name   = "${local.name}-artifacts-${data.aws_caller_identity.current.account_id}"
  force_destroy = false
  tags          = local.tags
}

module "iam" {
  source = "../../modules/iam"

  name           = local.name
  s3_bucket_arns = [module.artifacts_bucket.bucket_arn]
  tags           = local.tags
}

module "web" {
  source = "../../modules/ec2"

  name                  = "${local.name}-web"
  vpc_id                = module.vpc.vpc_id
  subnet_ids            = module.vpc.public_subnet_ids
  instance_count        = 2
  instance_type         = "t3.small"
  instance_profile_name = module.iam.instance_profile_name
  ingress_ports         = [80]
  allowed_cidrs         = var.allowed_cidrs
  user_data             = file("${path.module}/../../scripts/user_data.sh")
  tags                  = local.tags
}
