"""
response_builder.py — Translates raw cli/lib dicts into Pydantic response models.

Why this file exists:
  Each search method in engine.py returns a different dict shape (different keys,
  different field names). The frontend needs one consistent shape every time.
  This file normalizes all of them into SearchResult / SearchResponse.

The pattern in every builder function:
  1. Loop over raw results
  2. Extract the right fields (handling different key names per method)
  3. Build a SearchResult for each
  4. Wrap the list in a SearchResponse with timing + metadata
"""

import time
from backend.app.models.schemas import (
    SearchResult,
    SearchResponse,
    CompareResponse,
    ResultScores,
    ResultRanks,
)


def build_keyword_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
) -> SearchResponse:
    """Convert BM25 raw results into a SearchResponse.

    Raw dict shape from InvertedIndex.bm25_search():
      { id, title, document, score, metadata }
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["id"]),
            title=r["title"],
            snippet=r["document"][:200],       # truncate description to 200 chars
            rank=rank,
            scores=ResultScores(bm25=r["score"]),   # only bm25 score applies here
            ranks=ResultRanks(),                     # no rank info for single-method search
        ))

    return SearchResponse(
        query=query,
        method="keyword",
        limit=len(results),
        elapsed_ms=elapsed_ms,
        results=results,
    )


def build_semantic_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
) -> SearchResponse:
    """Convert chunked semantic raw results into a SearchResponse.

    Raw dict shape from ChunkedSemanticSearch.search_chunks():
      { id, title, document, score, metadata }
    Same shape as keyword — only difference is the score means cosine similarity.
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["id"]),
            title=r["title"],
            snippet=r["document"][:200],
            rank=rank,
            scores=ResultScores(semantic=r["score"]),   # cosine similarity score
            ranks=ResultRanks(),
        ))

    return SearchResponse(
        query=query,
        method="semantic",
        limit=len(results),
        elapsed_ms=elapsed_ms,
        results=results,
    )


def build_weighted_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
) -> SearchResponse:
    """Convert weighted hybrid raw results into a SearchResponse.

    Raw dict shape from HybridSearch.weighted_search():
      { doc_id, title, description, bm25_score, sem_score, hybrid_score }

    Note: field names differ here — 'doc_id' not 'id', 'description' not 'document'.
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["doc_id"]),               # different key name than keyword/semantic
            title=r["title"],
            snippet=r["description"][:200],    # different key name than keyword/semantic
            rank=rank,
            scores=ResultScores(
                bm25=r["bm25_score"],
                semantic=r["sem_score"],
                hybrid=r["hybrid_score"],
            ),
            ranks=ResultRanks(),               # weighted search doesn't track rank positions
        ))

    return SearchResponse(
        query=query,
        method="weighted",
        limit=len(results),
        elapsed_ms=elapsed_ms,
        results=results,
    )


def build_rrf_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
) -> SearchResponse:
    """Convert RRF hybrid raw results into a SearchResponse.

    Raw dict shape from HybridSearch.rrf_search():
      { doc_id, title, description, bm25_rank, sem_rank, rrf_score, bm25_score, sem_score }
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["doc_id"]),
            title=r["title"],
            snippet=r["description"][:200],
            rank=rank,
            scores=ResultScores(rrf=r["rrf_score"]),
            ranks=ResultRanks(
                bm25_rank=r["bm25_rank"],   # what position BM25 gave this movie
                sem_rank=r["sem_rank"],     # what position semantic gave this movie
            ),
        ))

    return SearchResponse(
        query=query,
        method="rrf",
        limit=len(results),
        elapsed_ms=elapsed_ms,
        results=results,
    )


def build_compare_response(
    query: str,
    limit: int,
    elapsed_ms: int,
    keyword: SearchResponse,
    semantic: SearchResponse,
    weighted: SearchResponse,
    rrf: SearchResponse,
) -> CompareResponse:
    """Wrap all four method responses into a single CompareResponse.

    Used by the /compare endpoint — runs all 4 searches in parallel,
    then combines their SearchResponse objects here.
    """
    return CompareResponse(
        query=query,
        limit=limit,
        elapsed_ms=elapsed_ms,
        methods={
            "keyword": keyword,
            "semantic": semantic,
            "weighted": weighted,
            "rrf": rrf,
        },
    )
