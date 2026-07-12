# ── Stage 1: Build frontend ─────────────────────────────────────
FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /build/frontend

# Install dependencies first (better layer caching)
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable pnpm && corepack prepare pnpm@10 --activate && pnpm install

# Copy source and build
COPY frontend/ ./
RUN pnpm build

# ── Stage 2: Build backend ──────────────────────────────────────
FROM ghcr.io/astral-sh/uv:0.7.10-python3.13-bookworm AS backend-builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_FROZEN=true

WORKDIR /build/backend

# Install dependencies first (better layer caching)
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy source and install the project itself
COPY backend/ ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ── Stage 3: Unified runtime ────────────────────────────────────
FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

WORKDIR /app

# ── Copy backend ─────────────────────────────────────────────────
COPY --from=backend-builder --chown=appuser:appuser /build/backend/.venv /app/.venv
COPY --from=backend-builder --chown=appuser:appuser /build/backend /app

# ── Copy frontend dist ───────────────────────────────────────────
COPY --from=frontend-builder --chown=appuser:appuser /build/frontend/dist /app/frontend-dist

# ── Copy nginx & supervisor config ───────────────────────────────
COPY backend/nginx.conf /etc/nginx/sites-available/default
COPY backend/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Remove default nginx site if it conflicts
RUN rm -f /etc/nginx/sites-enabled/default \
    && mkdir -p /etc/nginx/sites-enabled \
    && ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default \
    && mkdir -p /var/log/supervisor

# ── Runtime setup ────────────────────────────────────────────────
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN mkdir -p /app/.data && chown -R appuser:appuser /app/.data /app/frontend-dist /var/log/nginx /var/log/supervisor /var/lib/nginx

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
