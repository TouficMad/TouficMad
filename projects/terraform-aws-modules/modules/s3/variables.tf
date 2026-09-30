variable "bucket_name" {
  description = "Globally unique bucket name"
  type        = string
}

variable "versioning" {
  description = "Enable object versioning"
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow destroying the bucket even if it contains objects"
  type        = bool
  default     = false
}

variable "expire_noncurrent_after_days" {
  description = "Delete old object versions after N days (0 disables)"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags applied to the bucket"
  type        = map(string)
  default     = {}
}
