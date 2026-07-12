# Sentinel — Linux Health Monitor & Network Toolkit

Self-hosted health monitoring and network diagnostics for a mixed infrastructure fleet
(bare-metal, VMs, LXCs, Docker containers). Built as a DevOps pivot project.

## Structure
- `agent/` — runs on monitored hosts, collects metrics, performs diagnostics
- `api/` — FastAPI backend, ingests metrics, serves data, handles alerting
- `frontend/` — Next.js dashboard