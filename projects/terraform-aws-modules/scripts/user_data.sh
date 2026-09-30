#!/bin/bash
# Boot script for the web instances: installs Nginx and serves a status page.
set -euo pipefail

apt-get update -y
apt-get install -y nginx

TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)

cat > /var/www/html/index.html <<HTML
<h1>Deployed with Terraform</h1>
<p>Instance: ${INSTANCE_ID}</p>
<p>Availability zone: ${AZ}</p>
HTML

systemctl enable --now nginx
