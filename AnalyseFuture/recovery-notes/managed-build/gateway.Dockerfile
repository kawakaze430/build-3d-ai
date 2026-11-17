FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/build3d
COPY requirements.lock ./
COPY apps/gateway/ ./apps/gateway/
RUN --mount=type=secret,id=proxy_ca,required=true \
    PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir -c requirements.lock ./apps/gateway \
    && useradd --system --uid 10001 appuser
USER appuser
EXPOSE 8080
CMD ["uvicorn", "build3d_gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
