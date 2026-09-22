FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
RUN uv sync --frozen --no-dev && useradd --create-home atlas && mkdir /data && chown atlas:atlas /data
USER atlas
ENV PATH="/app/.venv/bin:$PATH" DATA_DIR=/data
EXPOSE 8000
# One worker: document indexing and conversation guards are process-local.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
