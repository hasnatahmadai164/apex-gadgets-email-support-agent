# Apex Gadgets Customer Support System

An AI-driven system that monitors a dedicated Gmail inbox for Apex Gadgets (an online phone and laptop store), triages incoming customer emails and either replies automatically, escalates to a human or filters the message out. Includes a small internal dashboard for daily operational stats.

## Architecture

**Two-stage triage before any specialist runs.** Every email first passes a relevance check, then a sensitivity check both on a small, cheap model. Only emails that clear both ever reach a specialist model. This keeps cost and risk low: nothing gets an automated reply unless it's confirmed relevant and confirmed safe.

**A hand-rolled LangGraph supervisor**, not the prebuilt `langgraph-supervisor` library, routes cleared emails to one of three specialists  RAG (product/policy Q&A), Orders or Tickets. Rolling it by hand keeps routing logic explicit: for example, checking whether a thread already has a pending order before ever calling an LLM to classify intent.

**Confirm-before-execute for anything that writes to the database.** Placing an order or opening a ticket never happens on a single email  the specialist replies with a summary and waits for the customer's next message to confirm. Email is inherently asynchronous and a misread intent shouldn't be able to create a real order.

**Postgres-backed LangGraph checkpointing, keyed on Gmail's thread ID.** The poller is stateless between runs by design  it matches how Azure Container Apps Jobs work, spinning up, doing one pass and exiting. So anything that needs to persist across separate emails (a pending order, RAG conversation history) is checkpointed externally rather than held in memory.

**Agentic retrieval for the RAG specialist** — retrieve, grade the result, rewrite the query and retry if the grade is weak, then answer. A single-shot retrieval silently fails when the first query phrasing doesn't match the knowledge base well; grading catches that before an answer is generated, at the cost of extra latency only when it's actually needed.

## Tech stack

Python 3.12 · LangChain / LangGraph · Azure AI Foundry (GPT-5-mini for specialists, text-embedding-3-small) · Pinecone · PostgreSQL + SQLAlchemy + Alembic · Gmail API · FastAPI · Docker · GitHub Actions · Azure Container Apps

## Project structure

```
app/
  core/         settings, shared schemas, LLM/embedding factories, graph state, checkpointer
  triage/       relevance and sensitivity classifiers
  agents/       rag, orders, tickets specialists, and the supervisor graph
  tools/        gmail, pinecone, order, and ticket integrations
  db/           SQLAlchemy models, session, Alembic migrations
  dashboard/    FastAPI server, template, static assets
  poller.py     scheduled entrypoint — one poll cycle per run
ingestion/      loads the knowledge base PDF into Pinecone
scripts/        one-off manual scripts (Gmail OAuth setup, smoke tests)
tests/          pytest suite — all LLM calls stubbed, no live network calls
```

## Local setup

```bash
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
docker compose up -d db
alembic upgrade head
python -m scripts.gmail_oauth_setup   # one-time, paste refresh token into .env
python -m ingestion.load_to_pinecone  # after placing data/knowledge_base.pdf
pytest
python -m app.poller                  # one poll cycle
uvicorn app.dashboard.server:app --reload
```

## Deployment

One Docker image, two entrypoints selected by command not by image: `python -m app.poller` (default) runs as a scheduled Azure Container Apps Job; `uvicorn app.dashboard.server:app` runs as an always-on Container App. Postgres runs as its own internal-only Container App in the same environment reachable only by the dashboard and poller, never the public internet. CI builds and pushes the image to `ghcr.io` on every push to `main`.


