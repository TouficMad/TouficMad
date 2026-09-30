variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "project" {
  description = "Project name used as a prefix for every resource"
  type        = string
  default     = "toufic-lab"
}

variable "allowed_cidrs" {
  description = "CIDRs allowed to reach the web servers"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
