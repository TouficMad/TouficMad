variable "name" {
  description = "Name prefix for IAM resources"
  type        = string
}

variable "s3_bucket_arns" {
  description = "Buckets the instances may read from and write to"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to IAM resources"
  type        = map(string)
  default     = {}
}
