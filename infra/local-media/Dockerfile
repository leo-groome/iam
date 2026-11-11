FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN uv pip install --system --no-cache fastapi "uvicorn[standard]" boto3 httpx pyjwt
WORKDIR /app
COPY gateway.py .
RUN adduser --disabled-password --gecos "" appuser
USER appuser
CMD ["uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8787"]
