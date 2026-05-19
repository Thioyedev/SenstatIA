from dotenv import load_dotenv
load_dotenv()

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import documents, health, query

app = FastAPI(
    title="SenStat API",
    description="Multi-agent RAG system for official Senegalese statistics",
    version="0.1.0",
)

# CORS: locked to explicit origins in production.
# Set ALLOWED_ORIGINS=https://your-frontend.com,https://other.com in .env
# Falls back to localhost only when unset (development).
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://localhost:8502")
_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(query.router)
app.include_router(documents.router)
app.include_router(health.router)
