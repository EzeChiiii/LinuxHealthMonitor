# agent/Dockerfile
# Multi-stage build, same pattern as the API. The agent additionally
# needs system-level network tools (ping, traceroute) installed via
# apt, since those aren't Python packages — psutil/dnspython/etc.
# only cover what's installable via pip.

# ---- Stage 1: build dependencies ----
FROM python:3.14-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Stage 2: final runtime image ----
FROM python:3.14-slim

WORKDIR /app

# Install system tools the diagnostics module shells out to.
# iputils-ping provides `ping`, traceroute provides `traceroute`.
# --no-install-recommends keeps this from pulling in extra bloat,
# and we clean up apt's cache afterward to keep the image slim.
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    traceroute \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY app/ ./app/

# Unlike the API, the agent isn't a web server — it's a long-running
# process with no ports to expose, so no EXPOSE line needed here.

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main"]