FROM python:3.13.10-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /bin/

RUN groupadd --system --gid 999 appuser \
    && useradd --system --gid 999 --uid 999 --create-home appuser

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app

RUN mkdir -p /models/hf_cache /models/cache \
    && chown -R appuser:appuser /app /models

USER appuser

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
