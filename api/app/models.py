# app/models.py
# SQLAlchemy models — Python classes that map to our database tables.
# These mirror the tables we created by hand in db/schema.sql.
# (In a more mature setup, we'd generate the schema FROM these models
# using Alembic migrations — we'll introduce that shortly. For now,
# we're keeping schema.sql and models.py in sync manually.)

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import Float

from sqlalchemy.dialects.postgresql import JSONB

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False)
    metric_type = Column(String, nullable=False)
    operator = Column(String, nullable=False)       # '>', '<', '>=', '<=', '='
    threshold = Column(Float, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    triggered_value = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="active")   # 'active', 'resolved'
    triggered_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)

class DiagnosticRun(Base):
    __tablename__ = "diagnostic_runs"

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False)
    diagnostic_type = Column(String, nullable=False)
    target = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    result = Column(JSONB, nullable=True)
    requested_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)


class Metric(Base):
    __tablename__ = "metrics"

    # Note: this is a simplified mapping. The real table has a composite
    # primary key (id, recorded_at) required by TimescaleDB — SQLAlchemy
    # can work with that, but for inserts specifically we don't need to
    # model that complexity yet. We'll revisit this if we hit issues.
    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False)
    metric_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    resource_type = Column(String, nullable=False)  # 'bare_metal', 'vm', 'lxc', 'docker'
    parent_host_id = Column(Integer, ForeignKey("hosts.id"), nullable=True)
    last_seen_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    