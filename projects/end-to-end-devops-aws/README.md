# End-to-End DevOps on AWS

A small Python API taken all the way from code to production: tested and containerized, provisioned on **AWS EKS with Terraform**, deployed by **GitHub Actions + Helm**, and monitored with **Prometheus + Grafana**.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?logo=amazonaws&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-0F1689?logo=helm&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white)

## Architecture

```
 Developer ──git push──► GitHub ──► GitHub Actions
                                     │ 1. flake8 + pytest
                                     │ 2. terraform validate, helm lint
                                     │ 3. docker build, smoke test, Trivy scan
                                     │ 4. push image ─────────────► Amazon ECR
                                     │ 5. helm upgrade (OIDC, no keys)
                                     ▼
                     ┌──────────── Amazon EKS ─────────────┐
 Users ──► AWS LB ──►│ taskapp pods (HPA 2→6)              │
                     │     ▲ /metrics                      │
                     │ Prometheus ──► Grafana dashboards   │
                     │     └──► alert rules                │
                     └─────────────────────────────────────┘
          VPC, EKS, node group, ECR, IAM: all Terraform
```

## Tech stack

| Area | Tools |
|---|---|
| Application | Python 3.12, Flask, Gunicorn, prometheus-client |
| Containers | Docker (multi-stage build, non-root user), Docker Compose |
| Infrastructure as code | Terraform: VPC, EKS, managed node group, ECR, IAM, GitHub OIDC |
| Orchestration | Kubernetes, Helm chart with probes, HPA, rolling updates, hardened security context |
| CI/CD | GitHub Actions: lint, test, build, smoke test, Trivy scan, deploy |
| Monitoring | Prometheus, Grafana, alert rules (availability, error rate, p95 latency) |

## Repository layout

```
app/                   Flask API, unit tests, Dockerfile
terraform/             VPC, EKS cluster + nodes, ECR, GitHub Actions OIDC role
helm/taskapp/          Helm chart (Deployment, Service, HPA)
monitoring/            Prometheus config + alerts, Grafana dashboard, k8s ServiceMonitor
scripts/               One-time cluster bootstrap (metrics-server, kube-prometheus-stack)
.github/workflows/     CI/CD pipeline
docker-compose.yml     Local stack: app + Prometheus + Grafana
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service info and version |
| GET | `/health` | Health check used by the Kubernetes probes |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create a task, `{"title": "..."}` |
| GET / PATCH / DELETE | `/api/tasks/<id>` | Read, update (`title`, `done`), delete |

## 1. Run locally

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana (admin / admin) | http://localhost:3000, dashboard **TaskApp Overview** |

Generate some traffic to see the graphs move:

```bash
curl -X POST localhost:8080/api/tasks -H 'Content-Type: application/json' -d '{"title":"learn EKS"}'
for i in $(seq 1 200); do curl -s localhost:8080/api/tasks > /dev/null; done
```

Run the tests without Docker:

```bash
cd app && pip install -r requirements-dev.txt && pytest -v
```

## 2. Provision AWS

> ⚠️ EKS costs around $0.10/hour for the control plane, plus the EC2 nodes. Run `terraform destroy` when you're done.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

If your AWS account already has a GitHub OIDC provider, import it first:
`terraform import aws_iam_openid_connect_provider.github arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com`

Then bootstrap the cluster (metrics-server, Prometheus/Grafana, app namespace):

```bash
./scripts/bootstrap-cluster.sh
```

## 3. Turn on continuous deployment

In **Settings → Secrets and variables → Actions**:

- Secret `AWS_ROLE_ARN` = `terraform -chdir=terraform output -raw github_actions_role_arn`
- Variable `AWS_ENABLED` = `true`

Also create a **production** environment under Settings → Environments. From then on, every push to `main` builds, pushes to ECR and runs `helm upgrade --atomic`. If the rollout fails, Helm rolls back automatically.

```bash
kubectl get svc taskapp -n taskapp   # EXTERNAL-IP is the public URL
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

## 4. Clean up

```bash
helm uninstall taskapp -n taskapp   # removes the load balancer
terraform -chdir=terraform destroy
```

## Security choices

- GitHub Actions uses **OIDC** to assume an IAM role. No AWS keys are stored in GitHub.
- The deploy role can only push to one ECR repo and edit one Kubernetes namespace.
- Containers run as non-root with a read-only filesystem and all capabilities dropped.
- ECR scans images on push, and Trivy scans them in CI.

## Next steps

- [ ] Store tasks in PostgreSQL (RDS) instead of memory, so all replicas share them
- [ ] Private subnets + NAT for the worker nodes
- [ ] Ingress with HTTPS (AWS Load Balancer Controller + ACM)
- [ ] GitOps deployment with Argo CD
