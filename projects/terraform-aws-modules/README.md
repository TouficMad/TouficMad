# Terraform AWS Modules

Reusable Terraform modules for AWS (VPC, EC2, S3, IAM), wired together into separate **dev** and **prod** environments and shipped through a **GitHub Actions** pipeline that checks, plans and applies the changes.

![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?logo=amazonaws&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

## Architecture

```
                    ┌──────────────────────── VPC (10.x.0.0/16) ────────────────────────┐
                    │                                                                    │
 Internet ──► IGW ──┼──► Public subnet AZ-a ──► EC2 (Nginx)    Public subnet AZ-b ──► EC2 │
                    │           │                                                        │
                    │        NAT GW (prod only)                                          │
                    │           ▼                                                        │
                    │    Private subnet AZ-a                 Private subnet AZ-b         │
                    └────────────────────────────────────────────────────────────────────┘
        EC2 ──(IAM instance profile: SSM + CloudWatch + S3)──► S3 artifacts bucket
```

## Repository layout

```
.
├── modules/
│   ├── vpc/        # VPC, public/private subnets across AZs, IGW, optional NAT
│   ├── ec2/        # Instances + security group, IMDSv2, encrypted gp3 root volume
│   ├── s3/         # Private, versioned, encrypted bucket with lifecycle rules
│   └── iam/        # EC2 role + instance profile (SSM, CloudWatch, scoped S3 access)
├── environments/
│   ├── dev/        # 1 × t3.micro, no NAT → cheap
│   └── prod/       # 2 × t3.small across AZs, NAT gateway
├── scripts/user_data.sh
└── .github/workflows/terraform.yml
```

## Modules

| Module | Main inputs | Outputs |
|---|---|---|
| `vpc` | `name`, `cidr_block`, `az_count`, `enable_nat_gateway` | `vpc_id`, `public_subnet_ids`, `private_subnet_ids` |
| `ec2` | `name`, `vpc_id`, `subnet_ids`, `instance_type`, `instance_count`, `ingress_ports` | `instance_ids`, `public_ips`, `security_group_id` |
| `s3` | `bucket_name`, `versioning`, `expire_noncurrent_after_days` | `bucket_id`, `bucket_arn` |
| `iam` | `name`, `s3_bucket_arns` | `role_name`, `instance_profile_name` |

Example usage:

```hcl
module "vpc" {
  source             = "../../modules/vpc"
  name               = "demo"
  cidr_block         = "10.0.0.0/16"
  enable_nat_gateway = false
}
```

## Getting started

Prerequisites: Terraform ≥ 1.5, AWS CLI with credentials (`aws configure`).

```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars   # set allowed_cidrs to your IP
terraform init
terraform plan
terraform apply

# open the web server
curl http://$(terraform output -json web_public_ips | jq -r '.[0]')

# clean up so you don't pay for idle resources
terraform destroy
```

Connect to an instance without SSH keys:

```bash
aws ssm start-session --target <instance-id>
```

## Remote state

Store state in S3 so the CI pipeline and your laptop share it:

```bash
aws s3api create-bucket --bucket <you>-tfstate --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1
aws s3api put-bucket-versioning --bucket <you>-tfstate --versioning-configuration Status=Enabled
```

Then uncomment the `backend "s3"` block in `environments/<env>/providers.tf` and run `terraform init -migrate-state`.

## CI/CD pipeline

| Trigger | Jobs |
|---|---|
| Pull request / push to `main` | `terraform fmt`, `validate` on every module and environment, `tflint` |
| Same, once AWS is connected | `plan` for dev and prod |
| Manual (`workflow_dispatch`) | `apply` to the selected environment, with GitHub Environment protection |

To connect the pipeline to AWS (no long-lived keys, uses OIDC):

1. In IAM, add an OIDC identity provider for `token.actions.githubusercontent.com`.
2. Create a role trusted by `repo:<your-user>/terraform-aws-modules:*` with the permissions Terraform needs.
3. In the repo settings add the secret `AWS_ROLE_ARN` and the variable `AWS_ENABLED=true`.
4. Create the `dev` and `prod` environments. Add required reviewers on `prod`.

## What I learned

- Designing reusable modules with clear inputs and outputs, and input validation
- Keeping environments separate while reusing the same code
- Security defaults: IMDSv2, encrypted volumes, S3 public access blocked, least-privilege IAM
- Keyless AWS authentication from GitHub Actions using OIDC
