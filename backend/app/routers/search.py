"""
routers/search.py — All /api/search/* HTTP endpoints.

Each endpoint follows the same pattern:
  1. FastAPI validates the request body using the schema (automatic)
  2. Record start time
  3. Run the search via engine (in a thread — search code is synchronous)
  4. Translate raw results via response_builder
  5. Return a Pydantic model (FastAPI serializes to JSON automatically)

Why run_in_executor?
  engine functions are synchronous (blocking). FastAPI is async. Running blocking
  code directly in an async function would freeze the event loop and block all
  other requests. run_in_executor offloads the blocking work to a thread pool,
  keeping the event loop free.
"""

import time
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException

from backend.app.models.schemas import (
    SearchRequest,
    WeightedSearchRequest,
    RrfSearchRequest,
    RagRequest,
    TermScoreRequest,
    TermScoreResult,
    ChunkRequest,
    ChunkResult,
    SearchResponse,
    CompareResponse,
    RagResponse,
)
from backend.app.services import engine
from backend.app.services.response_builder import (
    build_keyword_response,
    build_semantic_response,
    build_weighted_response,
    build_rrf_response,
    build_compare_response,
)

# One shared thread pool for all blocking search calls
# max_workers=4 means up to 4 searches can run simultaneously
_executor = ThreadPoolExecutor(max_workers=4)

# APIRouter groups all these endpoints under the same prefix
# main.py will mount this router at /api/search
router = APIRouter()


# ─────────────────────────────────────────────────────────────
# Helper: run a blocking function in the thread pool
# ─────────────────────────────────────────────────────────────

async def _run(fn, *args):
    """Run a synchronous function in the thread pool without blocking the event loop.

    Usage:  results = await _run(engine.keyword_search, query, limit)
    This is equivalent to: results = engine.keyword_search(query, limit)
    but non-blocking — other requests can be handled while this runs.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, partial(fn, *args))


# ─────────────────────────────────────────────────────────────
# Search endpoints
# ─────────────────────────────────────────────────────────────

@router.post("/keyword", response_model=SearchResponse)
async def keyword_search_endpoint(req: SearchRequest):
    """BM25 keyword search.

    Optional: pass enhance="spell"|"rewrite"|"expand" to rewrite the query first.
    """
    query = req.query

    # If query enhancement requested, rewrite query before searching
    if req.enhance:
        query = await _run(engine.enhance_query, query, req.enhance)

    start = time.monotonic()
    raw = await _run(engine.keyword_search, query, req.limit)
    elapsed = int((time.monotonic() - start) * 1000)

    return build_keyword_response(query, raw, elapsed)


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search_endpoint(req: SearchRequest):
    """Chunked semantic search using sentence embeddings."""
    query = req.query

    if req.enhance:
        query = await _run(engine.enhance_query, query, req.enhance)

    start = time.monotonic()
    raw = await _run(engine.semantic_search, query, req.limit)
    elapsed = int((time.monotonic() - start) * 1000)

    return build_semantic_response(query, raw, elapsed)


@router.post("/hybrid/weighted", response_model=SearchResponse)
async def weighted_search_endpoint(req: WeightedSearchRequest):
    """Weighted hybrid search. alpha=0.5 blends BM25 and semantic equally."""
    query = req.query

    if req.enhance:
        query = await _run(engine.enhance_query, query, req.enhance)

    start = time.monotonic()
    raw = await _run(engine.weighted_search, query, req.limit, req.alpha)
    elapsed = int((time.monotonic() - start) * 1000)

    return build_weighted_response(query, raw, elapsed)


@router.post("/hybrid/rrf", response_model=SearchResponse)
async def rrf_search_endpoint(req: RrfSearchRequest):
    """RRF hybrid search. k=60 is the standard smoothing constant."""
    query = req.query

    if req.enhance:
        query = await _run(engine.enhance_query, query, req.enhance)

    start = time.monotonic()
    raw = await _run(engine.rrf_search, query, req.limit, req.k)
    elapsed = int((time.monotonic() - start) * 1000)

    return build_rrf_response(query, raw, elapsed)


@router.post("/compare", response_model=CompareResponse)
async def compare_endpoint(req: SearchRequest):
    """Run all 4 search methods in parallel and return combined results.

    asyncio.gather runs all 4 searches simultaneously.
    Total time = slowest method, not sum of all methods.
    """
    query = req.query

    if req.enhance:
        query = await _run(engine.enhance_query, query, req.enhance)

    start = time.monotonic()

    # All 4 searches start at the same time and run in separate threads
    kw_raw, sem_raw, w_raw, rrf_raw = await asyncio.gather(
        _run(engine.keyword_search,  query, req.limit),
        _run(engine.semantic_search, query, req.limit),
        _run(engine.weighted_search, query, req.limit, 0.5),
        _run(engine.rrf_search,      query, req.limit, 60),
    )

    elapsed = int((time.monotonic() - start) * 1000)

    # Build individual responses with their own timing
    # (elapsed here is the wall-clock time for all 4 together)
    kw_resp  = build_keyword_response(query, kw_raw,  elapsed)
    sem_resp = build_semantic_response(query, sem_raw, elapsed)
    w_resp   = build_weighted_response(query, w_raw,  elapsed)
    rrf_resp = build_rrf_response(query, rrf_raw, elapsed)

    return build_compare_response(query, req.limit, elapsed, kw_resp, sem_resp, w_resp, rrf_resp)


@router.post("/rag", response_model=RagResponse)
async def rag_endpoint(req: RagRequest):
    """RAG: retrieve top docs, pass to LLM, return generated answer."""
    query = req.query
    enhanced_query = None

    if req.enhance:
        enhanced_query = await _run(engine.enhance_query, query, req.enhance)
        query = enhanced_query

    start = time.monotonic()
    answer = await _run(engine.rag_answer, query, req.limit, req.mode)
    elapsed = int((time.monotonic() - start) * 1000)

    return RagResponse(
        query=req.query,
        enhanced_query=enhanced_query,
        answer=answer,
        elapsed_ms=elapsed,
    )


# ─────────────────────────────────────────────────────────────
# Utility endpoints
# ─────────────────────────────────────────────────────────────

@router.post("/scores/term", response_model=TermScoreResult)
async def term_scores_endpoint(req: TermScoreRequest):
    """Return TF, IDF, TF-IDF, BM25 breakdown for one term in one document.

    Used by the Score Explorer panel in the Keyword Playground.
    """
    scores = await _run(engine.get_term_scores, req.doc_id, req.term)
    return TermScoreResult(
        term=req.term,
        doc_id=req.doc_id,
        **scores,   # unpacks tf, idf, tfidf, bm25_tf, bm25_idf, bm25
    )


@router.post("/chunk", response_model=ChunkResult)
async def chunk_endpoint(req: ChunkRequest):
    """Chunk a piece of text and return the chunks.

    Used by the Chunking Explorer in the Semantic Playground.
    """
    chunks = await _run(engine.chunk_text, req.text, req.chunk_size, req.mode)
    return ChunkResult(
        chunks=chunks,
        total_chunks=len(chunks),
        mode=req.mode,
    )


@router.get("/health")
async def health():
    """Quick check that the server is up and indexes are loaded."""
    return {
        "status": "ok",
        "indexes_loaded": engine._hs is not None,
    }
