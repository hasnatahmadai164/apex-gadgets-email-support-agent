FROM python:3.12-slim

WORKDIR /app

RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid appuser --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "if [ \"$SERVICE_MODE\" = \"dashboard\" ]; then exec uvicorn app.dashboard.server:app --host 0.0.0.0 --port 8000; else exec python -m app.poller; fi"]
