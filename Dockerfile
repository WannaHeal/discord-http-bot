FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable

# Copy the project into the image
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable

FROM public.ecr.aws/docker/library/python:3.11-slim

# Copy the environment, but not the source code
COPY --from=builder --chown=app:app /app/.venv /app/.venv

EXPOSE 8000

# Run the application
ENTRYPOINT [ \
    "/app/.venv/bin/uvicorn", \
        "--host", "0.0.0.0", \
        "discord_http_bot.main:app"]
