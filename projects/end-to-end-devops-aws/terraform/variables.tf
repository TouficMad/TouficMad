variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "name" {
  description = "Name used for the cluster and every related resource"
  type        = string
  default     = "taskapp"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.31"
}

variable "node_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}

variable "github_repository" {
  description = "owner/repo allowed to deploy through GitHub Actions OIDC"
  type        = string
  default     = "TouficMad/end-to-end-devops-aws"
}
