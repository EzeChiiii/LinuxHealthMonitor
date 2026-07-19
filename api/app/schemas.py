# app/schemas.py
# Pydantic schemas define what data looks like coming in (requests)
# and going out (responses) through the API. Kept separate from
# models.py (the database layer) so the API's public shape and the
# database's internal shape can evolve independently.

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import Any


class MetricResponse(BaseModel):
    id: int
    host_id: int
    metric_type: str
    value: float
    recorded_at: datetime

    class Config:
        from_attributes = True
# What the caller sends to create a new alert rule.
class AlertRuleCreate(BaseModel):
    host_id: int
    metric_type: str
    operator: str          # '>', '<', '>=', '<=', '='
    threshold: float
    enabled: bool = True

class AlertRuleResponse(BaseModel):
    id: int
    host_id: int
    metric_type: str
    operator: str
    threshold: float
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertEventResponse(BaseModel):
    id: int
    alert_rule_id: int
    triggered_value: float
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True

class DiagnosticResultUpdate(BaseModel):
    result: dict

class DiagnosticRunCreate(BaseModel):
    host_id: int
    diagnostic_type: str   # 'ping', 'traceroute', 'dns_lookup', 'port_check', 'http_check'
    target: str

class DiagnosticRunResponse(BaseModel):
    id: int
    host_id: int
    diagnostic_type: str
    target: str
    status: str
    result: Optional[Any]
    requested_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
# What the agent sends for each metric reading.
class MetricCreate(BaseModel):
    host_id: int
    metric_type: str   # e.g. 'cpu_percent', 'memory_percent'
    value: float


# What the agent sends when registering a new host.
class HostCreate(BaseModel):
    name: str
    resource_type: str  # 'bare_metal', 'vm', 'lxc', 'docker'
    parent_host_id: Optional[int] = None

# What the API sends back — includes fields the client didn't provide,
# like the generated id and timestamps.
class HostResponse(BaseModel):
    id: int
    name: str
    resource_type: str
    parent_host_id: Optional[int]
    last_seen_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True  # lets this read directly from a SQLAlchemy object