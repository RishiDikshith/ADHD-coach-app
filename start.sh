#!/bin/bash

# Note: The FastAPI backend is now imported directly into Streamlit to save memory on cloud deployments.
# We no longer spin up background Gunicorn workers.

# Start the Streamlit frontend (this will be the main process)
streamlit run frontend/app.py \
  --server.port $PORT \
  --server.address 0.0.0.0 \
  --server.enableCORS=false \
  --client.showErrorDetails=false \
  --logger.level=error \
  --client.toolbarMode=minimal