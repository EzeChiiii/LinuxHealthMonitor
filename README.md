# Sentinel

***A self-hosted Linux health monitoring platform with on-demand network diagnostics, deployed as production-shaped, cloud-native infrastructure — built end-to-end to demonstrate the full DevOps lifecycle: Terraform, Ansible, Kubernetes, CI/CD, and observability.***

[![CI/CD](https://github.com/EzeChiiii/LinuxHealthMonitor/actions/workflows/ci.yml/badge.svg)](https://github.com/EzeChiiii/LinuxHealthMonitor/actions/workflows/ci.yml)
![Terraform](https://img.shields.io/badge/Terraform-AWS-844FBA?logo=terraform&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-k3s-326CE5?logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-multi--stage-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-FastAPI-3776AB?logo=python&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Grafana-E6522C?logo=prometheus&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

## Purpose

Managing a mixed fleet of infrastructure — bare-metal hosts, Ubuntu virtual machines, containers — usually means SSHing into each machine individually just to check if it's healthy. Sentinel replaces that with one dashboard: live health metrics, historical trends, on-demand network diagnostics, and threshold-based alerting, all in one place.

More importantly, this project was built as a deliberate exercise in the full DevOps lifecycle — not just writing the application, but containerizing it, provisioning real cloud infrastructure for it, deploying it with Kubernetes (K3s), automating its delivery with CI/CD (Github Actions), and orchestrating it with industry-standard observability tooling.

## Architecture at a Glance

![Sentinel full architecture diagram — AWS/k3s cluster, homelab fleet, and CI/CD pipeline](docs/images/architecture-overview.png)

Sentinel runs across two genuinely separate environments, connected only by outbound network calls:

**AWS (the platform)** — a single EC2 instance running a self-managed k3s Kubernetes cluster, provisioned entirely with Terraform. This is where the actual application lives: the FastAPI backend, the Next.js frontend, Postgres, Redis, and the observability stack (Prometheus + Grafana). This is the publicly-reachable, always-authoritative part of the system.

**Proxmox homelab (the monitored fleet)** — a set of real Ubuntu VMs running on physical hardware at home, each each running a real healthcare interoperability application — MirthConnect (routes and transforms clinical messages between systems), HAPI-FHIR (a standards-based patient records API), and Orthanc (a medical imaging server for storing and retrieving X-rays/scans). A lightweight Python agent runs on each VM and reports its health outbound to the AWS-hosted API — the same way a monitoring agent would report to a SaaS observability platform in a real company.

![Proxmox home lab virtual machines](docs/images/proxmox.png)

![Home lab diagram](docs/images/homelab.png)

**The key architectural point:** these two environments never talk to each other directly except through that one outbound path (homelab agent → AWS API, over plain HTTPS). The homelab doesn't run any part of the application itself, and the Kubernetes cluster doesn't run on the homelab — it's entirely separate, cloud-hosted infrastructure, deliberately mirroring how a real company might monitor on-premises infrastructure from a centralized, cloud-hosted monitoring platform.

## Structure
- `agent/` — runs on monitored hosts, collects metrics, performs diagnostics
- `api/` — FastAPI backend, ingests metrics, serves data, handles alerting
- `frontend/` — Next.js dashboard

## Tech Stack

| Category | Tool / Technology | Purpose |
|---|---|---|
| **Cloud & Infrastructure** | AWS (EC2, VPC, Elastic IP, Security Groups, IAM) | Hosting the production environment |
| | Terraform | Infrastructure as Code — provisions all AWS resources |
| | Ansible | Server configuration — Docker, k3s, SSH hardening, deploy user |
| **Containerization & Orchestration** | Docker | Multi-stage builds for API, agent, and frontend images |
| | Kubernetes (k3s) | Single-node cluster running the full application |
| | Helm | Kubernetes package management — custom chart for all services |
| **CI/CD** | GitHub Actions | Automated build, scan, push, and deploy pipeline |
| | Trivy | Container image vulnerability scanning |
| | Gitleaks | Secret-scanning on every commit |
| | Docker Hub | Container image registry |
| **Backend** | Python | Core language for the API and monitoring agent |
| | FastAPI | REST API framework |
| | SQLAlchemy | ORM / database layer |
| **Frontend** | Next.js | React framework, App Router |
| | TypeScript | Type-safe frontend development |
| | Tailwind CSS | Styling |
| | Recharts | Data visualization (historical metric charts) |
| **Data Layer** | PostgreSQL + TimescaleDB | Primary database, with time-series optimization for metrics |
| | Redis | Pub/sub messaging for on-demand diagnostics |
| **Observability** | Prometheus | Metrics collection and alerting engine |
| | Grafana | Metrics visualization and dashboards |
| | kube-prometheus-stack | Prometheus/Grafana/Alertmanager Helm chart |
| **Networking** | FortiGate (firewall/router), FortiSwitch (FortiLink-managed) | VLAN segmentation and inter-VLAN routing for the homelab environment |
| **Monitored Infrastructure** | MirthConnect, HAPI-FHIR, Orthanc | Real healthcare interoperability applications monitored by the agent |

## Screenshots

**Host overview — live health status and auto-discovered infrastructure**

Sentinel's dashboard shows every monitored host at a glance, including Docker containers automatically discovered and nested under their parent VM (`hapi-fhir`, `hapi-fhir-postgres`, and `cadvisor` are all auto-discovered children of `hapi-fhir-vm`, a real Proxmox VM).

![Sentinel host overview dashboard, showing parent/child host hierarchy](docs/images/dashboard-hosts.png)

---

**PostgreSQL, observed through Prometheus and Grafana**

Rather than relying only on Sentinel's own metrics, the database itself is instrumented with `postgres_exporter` and scraped by Prometheus — giving real transaction rates, connection counts, and resource usage for the database powering the whole application.

![Grafana dashboard showing PostgreSQL transactions, connections, and resource usage](docs/images/dashboard-detail.png)

---

**A custom-built Grafana dashboard for the API**

Beyond the imported community dashboards, this panel was hand-built using raw PromQL against metrics exposed by the FastAPI backend itself — tracking request rate and p95 latency per endpoint.

![Custom Grafana dashboard showing API request rate and p95 latency by endpoint](docs/images/API_dashboard.png)

---

**Per-host historical metrics**

Clicking into any host — including real Proxmox VMs on the homelab fleet — shows its CPU, memory, and disk history over time.

![Per-host detail page showing CPU, memory, and disk history for hapi-fhir-vm](docs/images/hapi-fhir-vm_detail_charts.png)

---

**Per-pod resource usage across the application namespace**

Beyond application-level metrics, Prometheus and Grafana also provide direct visibility into every pod's actual resource footprint — CPU usage, network throughput, and packet rates — for `api`, `agent`, `frontend`, `postgres`, and `redis`, all running in the same Kubernetes namespace.

![Verifying the hosts table after recovery](docs/images/hosts-table.png)

![Verifying the hosts table after recovery](docs/images/pods.png)

![Grafana Kubernetes cluster dashboard](docs/images/Kubernetes-cluster.png)


**Alerts firing and resolving correctly throughout the recovery process:**

![Discord alert history showing alerts triggering and resolving](docs/images/discord-alerts.png)

## What I Built, Phase by Phase

This project was built as 16 sequential milestones, grouped into four phases — each phase proven working before moving to the next.

<details>
<summary><strong>Phase 1 — Application (Milestones 1–8)</strong>: built and proven entirely locally, before touching any cloud infrastructure</summary>

| Milestone | What was built |
|---|---|
| 1. Foundations | Monorepo structure, Python environments, Next.js scaffold, local Postgres/TimescaleDB and Redis via Docker |
| 2. Database schema | `hosts`, `metrics` (TimescaleDB hypertable), `diagnostic_runs`, `alert_rules`, `alert_events` |
| 3. API core | FastAPI service — host registration, metrics ingestion, shared-token authentication |
| 4. Agent — host metrics | Python agent collecting real CPU/memory/disk via `psutil` |
| 5. Agent — Docker metrics | Auto-discovery and reporting of Docker containers, nested under their parent host |
| 6. Diagnostics + Redis pub/sub | Ping, traceroute, DNS lookup, port check, HTTP check — triggerable on demand via Redis |
| 7. Alerting | Threshold-based alert rules, active/resolved state tracking, Discord webhook notifications |
| 8. Frontend dashboard | Next.js UI — host list, per-host historical charts, diagnostic panel, alert history |

</details>

<details>
<summary><strong>Phase 2 — Platform (Milestones 9–14)</strong>: containerized, deployed on real cloud infrastructure, with a fully automated delivery pipeline</summary>

| Milestone | What was built |
|---|---|
| 9. Containerization | Multi-stage Dockerfiles for all three services; full `docker-compose.yml` orchestration |
| 10. AWS provisioning | VPC, EC2, security groups, and an Elastic IP — provisioned entirely with Terraform |
| 11. Server configuration | Ansible playbooks — Docker, k3s, SSH hardening, a dedicated deploy user |
| 12. Kubernetes + Helm | A custom Helm chart deploying the full application to a self-managed k3s cluster |
| 13. Homelab agent rollout | Real Proxmox VMs (running MirthConnect, HAPI-FHIR, Orthanc) reporting metrics to the AWS-hosted API |
| 14. CI/CD pipeline | GitHub Actions — Gitleaks, Trivy, multi-platform Docker builds, automated deployment |

</details>

<details>
<summary><strong>Phase 3 — Observability (Milestone 15)</strong>: industry-standard monitoring for the infrastructure the application itself runs on</summary>

| Milestone | What was built |
|---|---|
| 15. Prometheus + Grafana | `kube-prometheus-stack`, `postgres_exporter` and `redis_exporter` sidecars, FastAPI instrumentation, and custom Grafana dashboards |

</details>


## A Real Incident I Hit and Resolved

<details>
<summary><strong>Postgres data loss during Helm chart editing</strong> — click to expand</summary>

**What happened:** While adding Prometheus exporter sidecars to the Helm chart, a template file (`postgres.yaml`) went missing on the deployment target due to drift between my local machine and the server — it had been deleted and recreated multiple times while debugging a YAML indentation error, and the correct version wasn't consistently synced back. A subsequent `helm upgrade` interpreted the file's absence as an intentional removal of Postgres from the desired cluster state, and deleted both the Postgres Deployment **and its PersistentVolumeClaim** — permanently erasing all application data (hosts, metrics, alert rules).

**Root cause:** Helm treats the contents of a chart's `templates/` directory, at the moment `helm upgrade` runs, as the complete and authoritative desired state — not as incremental additions. Editing files directly on the deployment target, rather than deploying from a single version-controlled source, created a window where the working copy silently diverged, with no warning before the destructive reconciliation.

**Detection:** Noticed indirectly — a Grafana dashboard built to visualize `postgres_exporter` metrics showed no data. Confirmed via `kubectl get pods`, `kubectl get pvc`, and `helm get manifest`, all showing Postgres entirely absent from the cluster's tracked state.

**Resolution:** Restored the correct `postgres.yaml` from my local, version-controlled copy, re-ran `helm upgrade` to recreate the Deployment and a fresh PersistentVolumeClaim, reapplied the database schema, and confirmed all hosts correctly re-registered with their parent/child relationships intact.


**What I changed as a result:**
- Never edit deployment files directly on a server again — all changes go through git, deployed from a single source of truth
- Database migrations (Alembic) moved up in priority — manual `schema.sql` reapplication is a real, avoidable risk
- Identified a real gap in the current CI/CD pipeline: it doesn't automate Helm chart deployment, only application code — see [Known Limitations](#known-limitations--what-id-do-differently-at-scale)


</details>

## Known Limitations & What I'd Do Differently at Scale

Every decision below was made deliberately, for a specific reason — usually cost-consciousness at this project's scale. Here's what I'd change if this were running in production with real traffic.

| Current approach | Why | What I'd do at production scale |
|---|---|---|
| Single-node k3s cluster (control plane + worker combined) | Avoids the cost of running dedicated control-plane infrastructure for a single-workload demo | A managed Kubernetes service (EKS), or a self-managed multi-node cluster with a dedicated, highly-available control plane |
| Postgres and Redis run in-cluster, self-managed | No RDS/ElastiCache costs; keeps everything within one Terraform-managed footprint | Amazon RDS (with automated backups, Multi-AZ failover) and ElastiCache — offloading database operations to a managed service |
| No autoscaling (fixed `replicas: 1` on every Deployment) | There's no real production traffic to scale against — adding the Horizontal Pod Autoscaler on a project with zero real load would be unverifiable, untested infrastructure | A node group with the Horizontal Pod Autoscaler, driven by real request-volume metrics |
| SSH temporarily open to `0.0.0.0/0` for GitHub Actions to reach the deploy target | The simplest way to get automated deployment working; GitHub-hosted runners use a large, rotating IP range that can't be safely allow-listed | A self-hosted GitHub Actions runner living inside the VPC, removing the need for any inbound SSH exposure at all |
| CI/CD automates application code only (`api/`, `agent/`, `frontend/`) — Helm/Terraform/Ansible changes are still applied manually | Infrastructure changes are infrequent enough that full GitOps wasn't the highest-priority milestone; a real incident (see postmortem) exposed the risk of this gap directly | Extend the pipeline to run `helm upgrade` automatically, or adopt a GitOps tool (ArgoCD/Flux) that continuously reconciles the cluster against the Git repository |
| Manual `schema.sql` application after any fresh database | Simple, fast to set up early in the project | Alembic-managed migrations — version-tracked, repeatable, safe to run against any environment |
| Homelab agents can report metrics but not receive on-demand diagnostic commands | Redis's pub/sub isn't exposed outside the cluster; opening it without adding authentication first would be a real, avoidable security gap | Expose Redis externally behind proper authentication (Redis AUTH or a dedicated message broker with TLS), or route the traffic through a VPN mesh |
| Single AWS region, no disaster recovery automation | Out of scope for a portfolio-scale project without real users to protect | Cross-region backups, Route 53 health-check-based failover, and a tested, documented recovery runbook (a lighter version of this already exists — see the incident postmortem) |


## Getting Started (Local Development)

The full stack runs locally via Docker Compose — no AWS account or cloud infrastructure required.

### Prerequisites

- Docker Desktop
- Git

### Setup

```bash
git clone https://github.com/EzeChiiii/LinuxHealthMonitor.git
cd LinuxHealthMonitor
```

Create the required `.env` files:

```bash
# api/.env
DATABASE_URL=postgresql+psycopg://sentinel:sentinel_dev_password@postgres:5432/sentinel
REDIS_URL=redis://redis:6379
AGENT_SHARED_TOKEN=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
DISCORD_WEBHOOK_URL=<optional — your own Discord webhook URL>

# agent/.env
API_URL=http://api:8000
REDIS_URL=redis://redis:6379
AGENT_SHARED_TOKEN=<same value as above>
HOST_NAME=local-dev-agent
REPORT_INTERVAL_SECONDS=10

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AGENT_TOKEN=<same value as above>
```

Start the full stack:

```bash
docker compose up -d --build
```

Apply the database schema (first run only):

```bash
docker exec -i sentinel_postgres psql -U sentinel -d sentinel < api/db/schema.sql
```

### Access

| Service | URL |
|---|---|
| Frontend dashboard | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |

### Verify it's working

```bash
curl http://localhost:8000/health
```

Should return `{"status":"ok"}`. The dashboard should show one host (`local-dev-agent`) reporting live metrics within about 10 seconds.


## Roadmap

This project is actively maintained. Planned next steps, roughly in priority order:

- [ ] **Alembic database migrations** — replace manual `schema.sql` application with proper, version-tracked migrations (directly motivated by the [Postgres incident](#a-real-incident-i-hit-and-resolved))
- [ ] **Resource requests/limits** on every Deployment, so no single pod can starve the node
- [ ] **Liveness and readiness probes** for the API and frontend
- [ ] **Self-hosted GitHub Actions runner** — removes the need for SSH to be reachable from the public internet during deploys
- [ ] **Extend CI/CD to cover infrastructure changes** — automatically apply Helm chart updates, not just application code
- [ ] **Redis exposed with proper authentication**, enabling on-demand diagnostics for the homelab-hosted agents
- [ ] **A second backup project** — an S3 + Lambda-based backup pipeline, doubling as a tested disaster-recovery path for this project's own Postgres data
- [ ] GitOps via ArgoCD or Flux, once the above CI/CD groundwork is in place
- [ ] A real domain name with TLS (Let's Encrypt), replacing the current raw IP + port setup