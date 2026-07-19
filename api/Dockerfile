# api/Dockerfile
# Multi-stage build: the first stage installs Python dependencies,
# the second stage copies only what's needed to actually run the app —
# keeps the final image slim by not shipping build tools/caches.

# ---- Stage 1: build dependencies ----
FROM python:3.14-slim AS builder

WORKDIR /app

# Copy only requirements first — this lets Docker cache this layer,
# so dependencies aren't reinstalled every time application code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Stage 2: final runtime image ----
FROM python:3.14-slim

WORKDIR /app

# Copy installed packages from the builder stage instead of reinstalling.
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy the actual application code.
COPY app/ ./app/

EXPOSE 8000

# Runs uvicorn without --reload (that's a dev-only feature — in
# production/containers, the process should just run once, stay up,
# and get restarted by Docker/Kubernetes if it crashes).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]