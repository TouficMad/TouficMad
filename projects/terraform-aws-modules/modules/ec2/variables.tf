variable "name" {
  description = "Name prefix for the instances"
  type        = string
}

variable "vpc_id" {
  description = "VPC to launch into"
  type        = string
}

variable "subnet_ids" {
  description = "Subnets to spread instances across"
  type        = list(string)
}

variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = 1
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "AMI to use. Empty means latest Ubuntu 24.04"
  type        = string
  default     = ""
}

variable "key_name" {
  description = "Existing EC2 key pair name for SSH (optional)"
  type        = string
  default     = null
}

variable "instance_profile_name" {
  description = "IAM instance profile to attach (optional)"
  type        = string
  default     = null
}

variable "user_data" {
  description = "Cloud-init / bash user data"
  type        = string
  default     = null
}

variable "ingress_ports" {
  description = "TCP ports to open"
  type        = list(number)
  default     = [22, 80]
}

variable "allowed_cidrs" {
  description = "CIDRs allowed to reach the ingress ports"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "root_volume_size" {
  description = "Root volume size in GiB"
  type        = number
  default     = 20
}

variable "tags" {
  description = "Tags applied to every resource"
  type        = map(string)
  default     = {}
}
