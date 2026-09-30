#!/usr/bin/env bash
# One-time cluster setup, run by the cluster admin after `terraform apply`:
# metrics-server (for the HPA), kube-prometheus-stack (Prometheus + Grafana),
# the app namespace and the ServiceMonitor that scrapes the app.
set -euo pipefail

cd "$(dirname "$0")/.."

REGION=$(terraform -chdir=terraform output -raw region)
CLUSTER=$(terraform -chdir=terraform output -raw cluster_name)

aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER"

helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword="${GRAFANA_PASSWORD:-change-me}" \
  --wait

kubectl create namespace taskapp --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f monitoring/k8s/servicemonitor.yaml

kubectl create configmap taskapp-dashboard -n monitoring \
  --from-file=taskapp.json=monitoring/grafana/dashboards/taskapp.json \
  --dry-run=client -o yaml | kubectl label -f - --local grafana_dashboard=1 -o yaml | kubectl apply -f -

echo
echo "Cluster ready. Open Grafana with:"
echo "  kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
