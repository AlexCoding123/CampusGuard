# ==========================================
# STAGE 1: Base Runtime Dependencies
# ==========================================
FROM python:3.12-slim-bookworm AS base

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# STAGE 2: UV Setup
# ==========================================
FROM base AS uv-base
COPY --from=ghcr.io/astral-sh/uv:0.10.3 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    PATH="/app/.venv/bin:$PATH"
 
# ==========================================
# STAGE 3: Production Builder (Built ONCE)
# ==========================================
FROM uv-base AS prod-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ==========================================
# STAGE 4: Development Builder (Inherits Prod)
# ==========================================
FROM prod-builder AS dev-builder
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# ==========================================
# STAGE 5: Production Runner
# ==========================================
FROM base AS final

COPY --from=prod-builder /app /app
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/app/entrypoint.sh"]