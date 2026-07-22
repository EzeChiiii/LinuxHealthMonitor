# app/main.py
# Entry point for the FastAPI application.
# app/main.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.auth import verify_agent_token
from app import models, schemas
import json
from app.redis_client import redis_client
from datetime import datetime, timezone
from app.notifications import send_discord_alert
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(title="Sentinel API")

# Exposes a /metrics endpoint with request counts, latencies, and
# status codes per route — automatically instrumented, no manual
# tracking needed for each endpoint.
Instrumentator().instrument(app).expose(app) 

@app.get("/health")
def health_check():
    return {"status": "ok"}

import json
from app.redis_client import redis_client

@app.get("/alert-events", response_model=list[schemas.AlertEventResponse])
def list_alert_events(db: Session = Depends(get_db), _: None = Depends(verify_agent_token)):
    # Most recent first, so active/recent alerts show up at the top.
    return (
        db.query(models.AlertEvent)
        .order_by(models.AlertEvent.triggered_at.desc())
        .all()
    )

# Allows the Next.js frontend (running on a different port) to make
# requests to this API from the browser. Without this, the browser
# blocks cross-origin requests before they even reach us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://3.234.48.52:3000"],  # frontend dev server and EC2 public IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/diagnostics/{diagnostic_run_id}", response_model=schemas.DiagnosticRunResponse)
def get_diagnostic_run(
    diagnostic_run_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    run = db.query(models.DiagnosticRun).filter(models.DiagnosticRun.id == diagnostic_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Diagnostic run not found")
    return run

@app.get("/hosts/by-id/{host_id}", response_model=schemas.HostResponse)
def get_host_by_id(host_id: int, db: Session = Depends(get_db), _: None = Depends(verify_agent_token)):
    host = db.query(models.Host).filter(models.Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@app.get("/hosts", response_model=list[schemas.HostResponse])
def list_hosts(db: Session = Depends(get_db), _: None = Depends(verify_agent_token)):
    return db.query(models.Host).all()


@app.post("/alert-rules", response_model=schemas.AlertRuleResponse)
def create_alert_rule(
    rule: schemas.AlertRuleCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    new_rule = models.AlertRule(
        host_id=rule.host_id,
        metric_type=rule.metric_type,
        operator=rule.operator,
        threshold=rule.threshold,
        enabled=rule.enabled,
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@app.post("/diagnostics/{diagnostic_run_id}/result", response_model=schemas.DiagnosticRunResponse)
def report_diagnostic_result(
    diagnostic_run_id: int,
    update: schemas.DiagnosticResultUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    run = db.query(models.DiagnosticRun).filter(models.DiagnosticRun.id == diagnostic_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Diagnostic run not found")

    # Update status based on whether the diagnostic itself succeeded —
    # note this is about whether the API successfully received/stored
    # the result, not whether the diagnostic found the target reachable
    # (e.g. a "failed" ping still gets status='completed', since the
    # diagnostic ran successfully and gave us a real answer).
    run.result = update.result
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(run)
    return run

@app.post("/diagnostics", response_model=schemas.DiagnosticRunResponse)
def trigger_diagnostic(
    diag: schemas.DiagnosticRunCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    # Create the diagnostic_runs row first, status='pending' by default.
    new_run = models.DiagnosticRun(
        host_id=diag.host_id,
        diagnostic_type=diag.diagnostic_type,
        target=diag.target,
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # Publish to that host's specific Redis channel, so only the
    # matching agent picks it up. The message just needs enough info
    # for the agent to act — the diagnostic_run id, type, and target.
    channel = f"diagnostics:host:{diag.host_id}"
    message = json.dumps({
        "diagnostic_run_id": new_run.id,
        "diagnostic_type": new_run.diagnostic_type,
        "target": new_run.target,
    })
    redis_client.publish(channel, message)

    return new_run


# GET endpoint to look up an existing host by name.
# Used by the agent to check "does this host already exist?"
# before trying to register it fresh.
@app.get("/hosts/{name}", response_model=schemas.HostResponse)
def get_host_by_name(
    name: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),   # keep consistent with every other endpoint
):
    host = db.query(models.Host).filter(models.Host.name == name).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host

# Registers a new host (or is called by a host announcing itself
# for the first time). Returns the created host record.
@app.post("/hosts", response_model=schemas.HostResponse)


def register_host(host: schemas.HostCreate, db: Session = Depends(get_db)):
    new_host = models.Host(
        name=host.name,
        resource_type=host.resource_type,
        parent_host_id=host.parent_host_id,
    )
    db.add(new_host)
    try:
        db.commit()
    except IntegrityError:
        # Happens if the name already exists (we set UNIQUE on it)
        # or parent_host_id doesn't reference a real host.
        db.rollback()
        raise HTTPException(status_code=400, detail="Host with this name already exists, or invalid parent_host_id")
    db.refresh(new_host)  # pulls back the auto-generated id, created_at, etc.
    return new_host

def evaluate_alert_rules(host_id: int, metric_type: str, value: float, db: Session):
    operators = {
        ">": lambda v, t: v > t,
        "<": lambda v, t: v < t,
        ">=": lambda v, t: v >= t,
        "<=": lambda v, t: v <= t,
        "=": lambda v, t: v == t,
    }

    rules = db.query(models.AlertRule).filter(
        models.AlertRule.host_id == host_id,
        models.AlertRule.metric_type == metric_type,
        models.AlertRule.enabled == True,
    ).all()

    for rule in rules:
        compare = operators[rule.operator]
        threshold_crossed = compare(value, rule.threshold)

        existing_active = db.query(models.AlertEvent).filter(
            models.AlertEvent.alert_rule_id == rule.id,
            models.AlertEvent.status == "active",
        ).first()

        if threshold_crossed and not existing_active:
            new_event = models.AlertEvent(
                alert_rule_id=rule.id,
                triggered_value=value,
                status="active",
        )
            db.add(new_event)
            db.commit()
            message = f"🔴 **Alert triggered** — host {host_id}: {metric_type} {rule.operator} {rule.threshold} (actual: {value})"
            print(message)
            send_discord_alert(message)

        elif not threshold_crossed and existing_active:
            existing_active.status = "resolved"
            existing_active.resolved_at = datetime.now(timezone.utc)
            db.commit()
            message = f"✅ **Alert resolved** — host {host_id}: {metric_type} back to {value} (threshold: {rule.operator} {rule.threshold})"
            print(message)
            send_discord_alert(message)

# app/main.py (add this)
@app.post("/metrics")
def ingest_metric(
    metric: schemas.MetricCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    new_metric = models.Metric(
        host_id=metric.host_id,
        metric_type=metric.metric_type,
        value=metric.value,
    )
    db.add(new_metric)

    # Update this host's last_seen_at so the dashboard can show
    # whether it's actively reporting or has gone quiet.
    host = db.query(models.Host).filter(models.Host.id == metric.host_id).first()
    if host:
        host.last_seen_at = datetime.now(timezone.utc)

    db.commit()

    evaluate_alert_rules(metric.host_id, metric.metric_type, metric.value, db)

    return {"status": "recorded"}

@app.get("/hosts/{host_id}/metrics", response_model=list[schemas.MetricResponse])
def get_host_metrics(
    host_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    # Returns the most recent 200 readings for this host, across all
    # metric types (cpu/memory/disk) — the frontend will split them
    # apart by metric_type when rendering separate graphs.
    return (
        db.query(models.Metric)
        .filter(models.Metric.host_id == host_id)
        .order_by(models.Metric.recorded_at.desc())
        .limit(200)
        .all()
    )