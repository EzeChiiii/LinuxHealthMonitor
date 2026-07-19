# app/auth.py
# Simple shared-token authentication between agents and the API.
# Not full user auth (no accounts, no JWTs) — just a single secret
# value that every agent must send, proving it's allowed to talk
# to this API. Good enough for a system where "users" are your
# own agents, not the general public.

from fastapi import Header, HTTPException
from app.config import settings

def verify_agent_token(x_agent_token: str = Header(...)):
    # FastAPI automatically reads a header called "X-Agent-Token"
    # from the incoming request and passes it in here.
    if x_agent_token != settings.agent_shared_token:
        raise HTTPException(status_code=401, detail="Invalid or missing agent token")