output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "github_actions_role_arn" {
  description = "Put this in the AWS_ROLE_ARN repository secret"
  value       = aws_iam_role.github_actions.arn
}

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.main.name}"
}

output "region" {
  value = var.region
}
