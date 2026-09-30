# Ansible + Jenkins Lab

A local lab for configuration management. **Jenkins** runs a pipeline that lints the **Ansible** code, does a dry run, waits for approval and then configures two Ubuntu servers: base setup, **Nginx** and **Prometheus node_exporter**. Everything runs on your laptop with **Docker Compose**, so there's no cloud bill.

![Ansible](https://img.shields.io/badge/Ansible-EE0000?logo=ansible&logoColor=white)
![Jenkins](https://img.shields.io/badge/Jenkins-D24939?logo=jenkins&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)

## Architecture

```
        ┌────────────── docker compose network ───────────────┐
        │                                                      │
 You ──►│ Jenkins :8080 ──(SSH + Ansible)──► web1 (Ubuntu, systemd) :8081
        │   pipeline from Jenkinsfile   └──► web2 (Ubuntu, systemd) :8082
        │                                        │ node_exporter :9100
        │ Prometheus :9090 ◄──── scrapes ────────┘                   │
        └──────────────────────────────────────────────────────┘
```

The "servers" are containers running **systemd and SSH**, so Ansible manages them the same way it would manage real VMs. You can point the inventory at EC2 instances instead and nothing else changes.

## Pipeline stages

| Stage | What it does |
|---|---|
| Prepare | Copies the SSH key, prints the Ansible version |
| Lint | `yamllint` and `ansible-lint` in parallel |
| Syntax check | `ansible-playbook --syntax-check` |
| Connectivity | `ansible all -m ping` |
| Dry run | `--check --diff` shows exactly what would change |
| Approve | Manual gate (skip with `AUTO_APPROVE`) |
| Deploy | Applies the playbook, then checks Nginx and node_exporter respond |

## Roles

| Role | Tasks |
|---|---|
| `common` | apt cache, base packages, timezone, admin users, MOTD |
| `nginx` | Installs Nginx, deploys a templated site and `/health` endpoint, reloads only on change |
| `node_exporter` | Creates a system user, installs a pinned release, systemd unit, restarts only on change |

All roles are **idempotent**. Run the playbook twice and the second run reports `changed=0`.

## Quick start

Prerequisites: Docker with Compose v2, running on Linux, or Docker Desktop on macOS/Windows.

```bash
git clone https://github.com/TouficMad/ansible-jenkins-lab.git
cd ansible-jenkins-lab
./setup.sh
```

1. Open Jenkins at http://localhost:8080 and log in as `admin` / `admin`. No setup wizard: plugins and the job come from [Configuration as Code](docker/jenkins/casc.yaml).
2. Open the **ansible-deploy** job and click **Build with Parameters**.
3. Review the dry run output, then click **Deploy**.
4. Visit http://localhost:8081 and http://localhost:8082.
5. In Prometheus (http://localhost:9090), query `node_load1` or `up{job="node"}`.

To have Jenkins build your fork, set `REPO_URL=https://github.com/<you>/ansible-jenkins-lab.git` before running `./setup.sh`.

### Run Ansible by hand

```bash
docker compose exec jenkins bash
cd /tmp && git clone https://github.com/TouficMad/ansible-jenkins-lab.git && cd ansible-jenkins-lab
cp /keys/id_ed25519 ~/.lab_key && chmod 600 ~/.lab_key
ansible all -m ping -e ansible_ssh_private_key_file=~/.lab_key
ansible-playbook site.yml --diff -e ansible_ssh_private_key_file=~/.lab_key
```

### Tear down

```bash
docker compose down -v
```

## Project layout

```
ansible.cfg
site.yml                      # main playbook + verification play
inventories/lab/              # hosts and group variables
roles/{common,nginx,node_exporter}
Jenkinsfile                   # declarative pipeline
docker/target/Dockerfile      # Ubuntu 24.04 + systemd + sshd
docker/jenkins/               # Jenkins image with Ansible, plugins, JCasC
docker-compose.yml
monitoring/prometheus.yml
```

## What I learned

- Writing reusable, idempotent Ansible roles with handlers, templates and defaults
- Using check mode and `--diff` as a safety net before changing servers
- Jenkins declarative pipelines: parameters, parallel stages, manual approval gates
- Jenkins Configuration as Code, so the whole CI server is rebuilt from Git
