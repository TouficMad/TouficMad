output "instance_ids" {
  description = "IDs of the instances"
  value       = aws_instance.this[*].id
}

output "public_ips" {
  description = "Public IPs of the instances"
  value       = aws_instance.this[*].public_ip
}

output "security_group_id" {
  description = "ID of the instance security group"
  value       = aws_security_group.this.id
}
