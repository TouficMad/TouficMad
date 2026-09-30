output "vpc_id" {
  value = module.vpc.vpc_id
}

output "web_public_ips" {
  value = module.web.public_ips
}

output "artifacts_bucket" {
  value = module.artifacts_bucket.bucket_id
}
