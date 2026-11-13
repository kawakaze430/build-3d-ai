FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/build3d
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir . && useradd --system --uid 10001 appuser
USER appuser
EXPOSE 8080
CMD ["uvicorn", "build3d_gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
