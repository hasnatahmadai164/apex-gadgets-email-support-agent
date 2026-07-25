#!/bin/sh
exec uvicorn app.dashboard.server:app --host 0.0.0.0 --port 8000
