"""
main.py — Creates the FastAPI app and wires everything together.

Responsibilities:
  1. Create the FastAPI application object
  2. Configure CORS (allow the frontend at localhost:3000 to call this API)
  3. Register the search router at /api/search
  4. Load all search indexes at startup via lifespan
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import search as search_router
from backend.app.services import engine


# ─────────────────────────────────────────────────────────────
# Lifespan — startup and shutdown logic
#
# @asynccontextmanager turns this into a context manager FastAPI can use.
# Code before `yield` runs at startup. Code after `yield` runs at shutdown.
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: load all indexes into memory before accepting any requests
    print("[startup] Loading search indexes...")
    engine.startup()
    print("[startup] Server ready.")

    yield  # server runs here — handling requests

    # SHUTDOWN: nothing to clean up (indexes just get garbage collected)
    print("[shutdown] Server stopping.")


# ─────────────────────────────────────────────────────────────
# App creation
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Observatory API",
    description="Search API powering the RAG Observatory — keyword, semantic, hybrid, and RAG search over movies.",
    version="1.0.0",
    lifespan=lifespan,   # wire in our startup/shutdown logic
)


# ─────────────────────────────────────────────────────────────
# CORS middleware
#
# Without this, the browser blocks requests from localhost:3000 → localhost:8000.
# We allow the local frontend origin during development.
# In production, replace with the actual deployed frontend URL.
# ─────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# Router registration
#
# include_router attaches all endpoints from search_router.router to this app.
# prefix="/api/search" means every route in the router gets that prefix:
#   router.post("/keyword")  →  POST /api/search/keyword
#   router.post("/compare")  →  POST /api/search/compare
#   router.get("/health")    →  GET  /api/search/health
# ─────────────────────────────────────────────────────────────

app.include_router(
    search_router.router,
    prefix="/api/search",
    tags=["search"],         # groups endpoints under "search" in /docs
)
