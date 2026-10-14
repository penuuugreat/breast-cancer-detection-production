# Build from the repo root: docker compose --profile orchestration up --build
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
COPY orchestration/requirements.txt orchestration/requirements.txt
RUN pip install --no-cache-dir -r orchestration/requirements.txt
COPY backend backend
COPY orchestration orchestration
ENV DAGSTER_HOME=/dagster_home
RUN mkdir -p $DAGSTER_HOME && printf 'telemetry:\n  enabled: false\n' > $DAGSTER_HOME/dagster.yaml
EXPOSE 3000
CMD ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000", "-f", "orchestration/definitions.py"]
