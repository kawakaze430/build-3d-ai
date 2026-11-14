FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/build3d
COPY requirements.lock ./
COPY apps/gateway/ ./apps/gateway/
COPY apps/api/ ./apps/api/
RUN pip install --no-cache-dir -c requirements.lock ./apps/gateway ./apps/api \
    && useradd --system --uid 10001 appuser \
    && mkdir -p /var/lib/build3d/artifacts \
    && chown -R appuser /var/lib/build3d
ENV ARTIFACT_DIR=/var/lib/build3d/artifacts
USER appuser
EXPOSE 8081
CMD ["uvicorn", "build3d_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8081"]
