#!/usr/bin/env bash
# Creates the SSH key the lab uses, then starts every container.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p keys
if [[ ! -f keys/id_ed25519 ]]; then
  ssh-keygen -t ed25519 -N "" -C "ansible-lab" -f keys/id_ed25519
fi
# The Jenkins container runs as uid 1000 and must be able to read the private key
chmod 644 keys/id_ed25519

docker compose up -d --build

echo
echo "Jenkins:    http://localhost:8080  (admin / admin)"
echo "web1:       http://localhost:8081"
echo "web2:       http://localhost:8082"
echo "Prometheus: http://localhost:9090"
