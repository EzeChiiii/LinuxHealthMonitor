# frontend/Dockerfile
# Multi-stage build: first stage installs deps and runs Next.js's
# production build; second stage copies only the built output into
# a slim runtime image. Unlike dev mode (npm run dev), this compiles
# everything ahead of time instead of recompiling on every request.

# ---- Stage 1: build ----
FROM node:22-slim AS builder

WORKDIR /app

# Copy package files first, so dependency installs get cached
# separately from application code changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# These are baked into the build at build-time, since Next.js embeds
# NEXT_PUBLIC_ vars into the compiled JavaScript itself — they can't
# be swapped at runtime the way backend env vars can.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_AGENT_TOKEN
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_AGENT_TOKEN=$NEXT_PUBLIC_AGENT_TOKEN

RUN npm run build

# ---- Stage 2: runtime ----
FROM node:22-slim

WORKDIR /app

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["npm", "start"]