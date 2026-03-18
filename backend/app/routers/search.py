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

from fastapi import APIRouter

from backend.app.models.schemas import (
    SearchRequest,
    WeightedSearchRequest,
    RrfSearchRequest,
    RerankRequest,
    RagRequest,
    SearchResponse,
    RagResponse,
)
from backend.app.services import engine
from backend.app.services.response_builder import (
    build_keyword_response,
    build_bm25_response,
    build_doc_semantic_response,
    build_chunked_semantic_response,
    build_weighted_response,
    build_rrf_response,
    build_rerank_response,
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
    """Inverted index keyword search — Chapter 1.

    Tokenizes the query, finds all documents in the inverted index that contain
    any query token (in title or description), returns first `limit` matches.
    No scoring — results are in index order, not relevance order.
    """
    start = time.monotonic()
    raw = await _run(engine.keyword_search, req.query, req.limit)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_keyword_response(req.query, raw, elapsed)


@router.post("/bm25", response_model=SearchResponse)
async def bm25_search_endpoint(req: SearchRequest):
    """BM25 keyword search — Chapter 2.

    Same inverted index as keyword search, but every result now has a score.
    Results are ranked best-match-first using the BM25 formula:
      score = IDF(term) × (TF × (k1+1)) / (TF + k1 × (1 - b + b × doc_len/avg_len))

    Higher score = stronger match based on term frequency, rarity, and document length.
    """
    start = time.monotonic()
    raw = await _run(engine.bm25_search, req.query, req.limit)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_bm25_response(req.query, raw, elapsed)


@router.post("/semantic", response_model=SearchResponse)
async def doc_semantic_search_endpoint(req: SearchRequest):
    """Document-level semantic search — Chapter 3.

    One embedding per full movie description. Ranks by cosine similarity to query.
    No word matching — understands meaning. "astronaut left on Mars" matches
    "man stranded on hostile planet" even with zero word overlap.
    """
    start = time.monotonic()
    raw = await _run(engine.doc_semantic_search, req.query, req.limit)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_doc_semantic_response(req.query, raw, elapsed)


@router.post("/semantic/chunked", response_model=SearchResponse)
async def chunked_semantic_search_endpoint(req: SearchRequest):
    """Chunked semantic search — Chapter 4.

    One embedding per sentence chunk. The best matching chunk per movie wins.
    More granular than document-level — specific sentences score higher than
    averaged whole-document embeddings.
    """
    start = time.monotonic()
    raw = await _run(engine.chunked_semantic_search, req.query, req.limit)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_chunked_semantic_response(req.query, raw, elapsed)


@router.post("/hybrid/weighted", response_model=SearchResponse)
async def weighted_search_endpoint(req: WeightedSearchRequest):
    """Weighted hybrid search — Chapter 5.

    Blends BM25 and semantic scores:
      final_score = alpha * norm(bm25_score) + (1 - alpha) * norm(semantic_score)

    alpha=1.0 → pure BM25
    alpha=0.0 → pure semantic
    alpha=0.5 → equal blend (default)

    Both score lists are normalized to [0,1] before blending so they are
    on the same scale. The result combines keyword precision with semantic meaning.
    """
    start = time.monotonic()
    raw = await _run(engine.weighted_search, req.query, req.limit, req.alpha)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_weighted_response(req.query, raw, elapsed)


@router.post("/hybrid/rrf", response_model=SearchResponse)
async def rrf_search_endpoint(req: RrfSearchRequest):
    """RRF hybrid search — Chapter 6.

    Fuses BM25 and semantic rank positions using Reciprocal Rank Fusion:
      rrf_score = 1/(bm25_rank + k) + 1/(sem_rank + k)

    k=60 is the standard smoothing constant — prevents top ranks from
    dominating too strongly. Higher k = smoother blending.

    Unlike weighted search, RRF never looks at raw scores — only rank positions.
    A movie ranked #1 by BM25 and #3 by semantic gets a very high RRF score
    regardless of what the actual scores were.

    Optional: pass enhance="spell"|"rewrite"|"expand" to rewrite query via LLM first.
    """
    query = req.query
    if req.enhance:
        query = await _run(engine.enhance_query, query, req.enhance)

    start = time.monotonic()
    raw = await _run(engine.rrf_search, query, req.limit, req.k)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_rrf_response(query, raw, elapsed)


@router.post("/rerank/batch", response_model=SearchResponse)
async def batch_rerank_endpoint(req: RerankRequest):
    """Batch semantic re-ranking — Chapter 7.

    Stage 1: RRF retrieves `retrieval_limit` candidates (fast, imprecise)
    Stage 2: Bi-encoder re-scores all candidates in one batch (precise)

    The re-ranking score replaces the RRF score for final ordering.
    Response includes both rrf_score (before) and rerank_score (after)
    so you can see how positions changed.
    """
    start = time.monotonic()
    raw = await _run(engine.batch_rerank, req.query, req.limit, req.retrieval_limit)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_rerank_response(req.query, raw, elapsed, "batch_rerank")


@router.post("/rerank/cross-encoder", response_model=SearchResponse)
async def cross_encoder_rerank_endpoint(req: RerankRequest):
    """Cross-encoder re-ranking — Chapter 8.

    Stage 1: RRF retrieves `retrieval_limit` candidates (fast)
    Stage 2: Cross-encoder scores each (query, document) pair together (most accurate)

    Cross-encoder sees query and document as one input — captures interactions
    that bi-encoders miss. Best possible ranking quality, highest latency.
    """
    start = time.monotonic()
    raw = await _run(engine.cross_encoder_rerank, req.query, req.limit, req.retrieval_limit)
    elapsed = int((time.monotonic() - start) * 1000)
    return build_rerank_response(req.query, raw, elapsed, "cross_encoder_rerank")


@router.post("/rag", response_model=RagResponse)
async def rag_endpoint(req: RagRequest):
    """RAG — Chapter 7: Retrieve → Augment → Generate.

    Step 1 (Retrieve):  RRF search finds top `limit` relevant movies
    Step 2 (Augment):   retrieved descriptions become context for the LLM
    Step 3 (Generate):  LLM reads the context and answers the query

    Four modes:
      answer   → direct answer to the query using retrieved context (default)
      summary  → summarize the retrieved movies as a group
      citation → answer with explicit citations to source movies
      question → generate follow-up questions based on retrieved context

    Requires GEMINI_API_KEY in environment.
    """
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


@router.get("/health")
async def health():
    """Quick check that the server is up and indexes are loaded."""
    return {
        "status": "ok",
        "indexes_loaded": engine._hs is not None,
    }
