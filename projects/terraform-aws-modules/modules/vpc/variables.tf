variable "name" {
  description = "Name prefix for all VPC resources"
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "cidr_block must be a valid IPv4 CIDR."
  }
}

variable "az_count" {
  description = "Number of availability zones to spread subnets across"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Create a single NAT gateway so private subnets can reach the internet (costs money)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags applied to every resource"
  type        = map(string)
  default     = {}
}
