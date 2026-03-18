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
    """Convert inverted index keyword search results into a SearchResponse.

    Chapter 1: basic keyword search — inverted index, no scoring.

    Raw dict shape from docmap (movies.json):
      { id, title, description }

    No score field — every matching document is treated equally.
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["id"]),
            title=r["title"],
            snippet=r.get("description", "")[:200],
            rank=rank,
            scores=ResultScores(),   # all null — no scoring in keyword search
            ranks=ResultRanks(),
        ))

    return SearchResponse(
        query=query,
        method="keyword",
        limit=len(results),
        elapsed_ms=elapsed_ms,
        results=results,
    )


def build_bm25_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
) -> SearchResponse:
    """Convert BM25 search results into a SearchResponse.

    Chapter 2: BM25 — same inverted index, but now every result has a score.

    Raw dict shape from InvertedIndex.bm25_search():
      { id, title, document, score, metadata }

    Note: the description field is called "document" here (not "description").
    This is how cli/lib/keyword_search.py returns it via format_search_result().
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["id"]),
            title=r["title"],
            snippet=r["document"][:200],          # "document" key, not "description"
            rank=rank,
            scores=ResultScores(bm25=r["score"]), # BM25 score — now we have a real number
            ranks=ResultRanks(),
        ))

    return SearchResponse(
        query=query,
        method="bm25",
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


def build_doc_semantic_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
) -> SearchResponse:
    """Convert document-level semantic search results into a SearchResponse.

    Chapter 3: one embedding per full document.

    Raw dict shape (built in engine.doc_semantic_search):
      { id, title, document, score }

    Score is cosine similarity — ranges from -1 to 1, higher = more similar.
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["id"]),
            title=r["title"],
            snippet=r["document"][:200],
            rank=rank,
            scores=ResultScores(semantic=r["score"]),  # cosine similarity score
            ranks=ResultRanks(),
        ))

    return SearchResponse(
        query=query,
        method="semantic",
        limit=len(results),
        elapsed_ms=elapsed_ms,
        results=results,
    )


def build_chunked_semantic_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
) -> SearchResponse:
    """Convert chunked semantic search results into a SearchResponse.

    Chapter 4: one embedding per sentence chunk, best chunk wins per movie.

    Raw dict shape from ChunkedSemanticSearch.search_chunks():
      { id, title, document, score, metadata }

    Score is cosine similarity of the best matching chunk, not the whole document.
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["id"]),
            title=r["title"],
            snippet=r["document"][:200],
            rank=rank,
            scores=ResultScores(semantic=r["score"]),  # best chunk's cosine similarity
            ranks=ResultRanks(),
        ))

    return SearchResponse(
        query=query,
        method="chunked",
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


def build_rerank_response(
    query: str,
    raw_results: list[dict],
    elapsed_ms: int,
    method: str,   # "batch_rerank" or "cross_encoder_rerank"
) -> SearchResponse:
    """Convert re-ranked results into a SearchResponse.

    Raw results come from rrf_search (so they have rrf_score, bm25_rank, sem_rank)
    with an added rerank_score field from the re-ranking stage.

    We store both: rrf_score (where it ranked before) and rerank_score (final score).
    This lets the frontend show how re-ranking changed the order.
    """
    results = []
    for rank, r in enumerate(raw_results, start=1):
        results.append(SearchResult(
            id=str(r["doc_id"]),
            title=r["title"],
            snippet=r.get("description", "")[:200],
            rank=rank,
            scores=ResultScores(
                rrf=r.get("rrf_score"),          # original RRF score before re-ranking
                rerank=r.get("rerank_score"),    # new score after re-ranking
            ),
            ranks=ResultRanks(
                bm25_rank=r.get("bm25_rank"),
                sem_rank=r.get("sem_rank"),
            ),
        ))

    return SearchResponse(
        query=query,
        method=method,
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
