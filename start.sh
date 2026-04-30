#!/bin/bash

# Start the FastAPI backend with Gunicorn (a production-ready server)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.main_api:app --bind 0.0.0.0:8000 &

# Start the Streamlit frontend (this will be the main process)
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS=false