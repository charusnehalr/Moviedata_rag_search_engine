"""
engine.py — The search engine singleton.

Creates one HybridSearch instance at server startup, holds it in memory,
and exposes clean functions the router can call.

Why a singleton?
  HybridSearch.__init__ loads ~250MB of data (BM25 index + chunk embeddings + model).
  Doing that once at startup means every request is fast — no disk I/O per query.
"""

import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# sys.path fix — must happen BEFORE any cli/lib imports
#
# cli/lib/*.py use "from lib.X import Y" which only works when
# the "cli/" directory is on Python's module search path.
#
# Path(__file__).parents[3] climbs up from engine.py:
#   [0] services/  [1] app/  [2] backend/  [3] rag-search-engine/
# Then / "cli" appends the cli folder.
# ─────────────────────────────────────────────────────────────
_CLI_PATH = Path(__file__).parents[3] / "cli"
if str(_CLI_PATH) not in sys.path:
    sys.path.insert(0, str(_CLI_PATH))

# These imports now resolve because cli/ is on sys.path
from lib.search_utils import load_movies
from lib.hybrid_search import HybridSearch
from lib.semantic_search import SemanticSearch


# ─────────────────────────────────────────────────────────────
# Module-level singletons
# _hs           → HybridSearch (BM25 index + ChunkedSemanticSearch)
# _sem          → SemanticSearch (document-level embeddings, separate instance)
# _cross_encoder → CrossEncoder model for precise re-ranking
# ─────────────────────────────────────────────────────────────
_hs: HybridSearch | None = None
_sem: SemanticSearch | None = None


def startup() -> None:
    """Load all indexes into memory. Called ONCE when the server boots.

    After this runs:
      _hs.idx              → BM25 InvertedIndex (ready for keyword + BM25 search)
      _hs.semantic_search  → ChunkedSemanticSearch (chunk embeddings, document_map keyed by integer position)
      _sem                 → SemanticSearch (document embeddings, document_map keyed by doc_id)

    Why two separate semantic objects?
      ChunkedSemanticSearch.document_map  uses integer position as key.
      SemanticSearch.document_map         uses doc_id as key.
      Loading both on the same object would let the second overwrite document_map,
      causing search_chunks to return wrong movies (same scores, different titles).
    """
    global _hs, _sem

    print("[engine] Loading movies...")
    movies = load_movies()

    print("[engine] Initializing HybridSearch (BM25 index + chunk embeddings)...")
    _hs = HybridSearch(movies)

    print("[engine] Loading document-level embeddings (separate SemanticSearch instance)...")
    _sem = SemanticSearch()
    _sem.load_or_create_embeddings(movies)

    print("[engine] Ready.")


# ─────────────────────────────────────────────────────────────
# Search functions
# Each one delegates to the appropriate method on _hs.
# The router calls these — it never touches _hs directly.
# ─────────────────────────────────────────────────────────────

def keyword_search(query: str, limit: int) -> list[dict]:
    """Inverted index keyword search — Chapter 1 of the timeline.

    This is the `search` command from keyword_search_cli.py.

    How it works:
      1. Tokenize the query (lowercase, remove stopwords, stem words)
         e.g. "man stranded planet" → ["man", "strand", "planet"]
      2. Look up each token in the inverted index to get matching doc IDs
         e.g. "planet" → [doc42, doc107, doc891, ...]
      3. Return the first `limit` unique movies found

    Searches both title AND description — the index was built from both fields.
    No scoring — every matching movie is treated equally.
    Order is determined by which doc ID appears first in the index, not relevance.

    Returns: list of raw movie dicts { id, title, description }
    """
    from lib.keyword_search import tokenize_text
    query_tokens = tokenize_text(query)
    seen = set()
    results = []
    for token in query_tokens:
        # get_documents(token) returns all doc IDs that contain this token
        for doc_id in _hs.idx.get_documents(token):
            if doc_id in seen:
                continue
            seen.add(doc_id)
            # docmap maps doc_id → raw movie dict { id, title, description }
            results.append(_hs.idx.docmap[doc_id])
            if len(results) >= limit:
                return results
    return results


def bm25_search(query: str, limit: int) -> list[dict]:
    """BM25 search — Chapter 2 (implemented later).

    Returns: list of { id, title, document, score, metadata }
    """
    return _hs.idx.bm25_search(query, limit)


def doc_semantic_search(query: str, limit: int) -> list[dict]:
    """Document-level semantic search — Chapter 3.

    This is the CLI `semantic search` command.

    Each movie has ONE embedding representing its full title + description.
    The query is embedded and compared against all 8000 movie embeddings.
    The most similar movies (by cosine similarity) are returned.

    Problem with this approach: one long description gets averaged into a single
    vector. Specific details get diluted. A movie about "space survival" might
    score lower than expected if its description also covers comedy, romance, etc.

    NOTE: SemanticSearch.search() does not return an `id` field — only title and
    description. We add the id back by looking up the title in the documents list.

    Returns: list of { id, title, document, score }
    """
    raw = _sem.search(query, limit)

    # search() returns {score, title, description} — no id.
    # Build a title → id map from _sem.documents (the list passed at startup).
    title_to_id = {m["title"]: str(m["id"]) for m in _sem.documents}

    results = []
    for r in raw:
        results.append({
            "id":       title_to_id.get(r["title"], "unknown"),
            "title":    r["title"],
            "document": r["description"],   # normalize key to "document"
            "score":    r["score"],
        })
    return results


def chunked_semantic_search(query: str, limit: int) -> list[dict]:
    """Chunked semantic search — Chapter 4.

    This is the CLI `semantic search_chunked` command.

    Each movie description is split into sentence-sized chunks. Each chunk gets
    its own embedding. The best matching chunk per movie determines the movie's score.

    Why this is better than document-level: a specific sentence about "surviving on Mars"
    scores highly for a space survival query even if the rest of the description is
    about romance or comedy — the best chunk wins, not the average of all chunks.

    Returns: list of { id, title, document, score, metadata }
    """
    return _hs.semantic_search.search_chunks(query, limit)


def weighted_search(query: str, limit: int, alpha: float) -> list[dict]:
    """Weighted hybrid: alpha * norm(bm25) + (1-alpha) * norm(semantic).

    alpha=1.0 → pure BM25 | alpha=0.0 → pure semantic | alpha=0.5 → equal blend
    Returns: list of { doc_id, title, description, bm25_score, sem_score, hybrid_score }

    Why slice here?
    combine_search_results() in hybrid_search.py never applies a limit — it returns
    all merged results sorted by hybrid score. The limit param only controls the
    candidate pool size (limit*500), not the output size. We slice ourselves.
    """
    return _hs.weighted_search(query, alpha, limit)[:limit]


def rrf_search(query: str, limit: int, k: int) -> list[dict]:
    """Reciprocal Rank Fusion: 1/(bm25_rank + k) + 1/(sem_rank + k).

    Returns: list of { doc_id, title, description, bm25_rank, sem_rank, rrf_score }
    """
    return _hs.rrf_search(query, k, limit)


def batch_rerank(query: str, limit: int, retrieval_limit: int | None = None) -> list[dict]:
    """LLM batch re-ranking — delegates directly to cli/lib/rerank.py:batch_rerank().

    Stage 1: RRF retrieves candidates
    Stage 2: ONE Gemini LLM call ranks all candidates using the batch_rerank.md prompt

    Lazy import: lib.rerank raises RuntimeError at module load if GEMINI_API_KEY missing.
    """
    from lib.rerank import batch_rerank as cli_batch_rerank

    pool = retrieval_limit if retrieval_limit is not None else limit * 5
    candidates = rrf_search(query, pool, k=60)
    if not candidates:
        return []

    # Delegates entirely to the CLI function — uses batch_rerank.md prompt + Gemini
    reranked = cli_batch_rerank(query, candidates)

    # CLI returns rerank_score as position index (0=best, lower is better)
    # Normalize to [0,1] with 1=best so the frontend can treat higher=better consistently
    n = len(reranked)
    for i, r in enumerate(reranked):
        r["rerank_score"] = round((n - 1 - i) / max(n - 1, 1), 4)

    return reranked[:limit]


def cross_encoder_rerank(query: str, limit: int, retrieval_limit: int | None = None) -> list[dict]:
    """Cross-encoder re-ranking — delegates directly to cli/lib/rerank.py:cross_encoder_rerank().

    Stage 1: RRF retrieves candidates
    Stage 2: ms-marco-TinyBERT-L2-v2 scores each (query, title+document) pair

    No LLM — pure ML model, deterministic, no API key needed.
    """
    from lib.rerank import cross_encoder_rerank as cli_cross_encoder_rerank

    pool = retrieval_limit if retrieval_limit is not None else limit * 5
    candidates = rrf_search(query, pool, k=60)
    if not candidates:
        return []

    # Delegates entirely to the CLI function — uses TinyBERT cross-encoder
    reranked = cli_cross_encoder_rerank(query, candidates)

    # CLI stores the score as cross_encoder_score — normalize key to rerank_score
    for r in reranked:
        r["rerank_score"] = float(r.get("cross_encoder_score", 0))

    return reranked[:limit]


# ─────────────────────────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────────────────────────

def get_term_scores(doc_id: int, term: str) -> dict:
    """TF, IDF, TF-IDF, BM25 breakdown for one term in one document.

    Used by the Score Explorer panel in the Keyword Playground.
    """
    return {
        "tf":      _hs.idx.get_tf(doc_id, term),
        "idf":     _hs.idx.get_idf(term),
        "tfidf":   _hs.idx.get_tfidf(doc_id, term),
        "bm25_tf": _hs.idx.get_bm25_tf(doc_id, term),
        "bm25_idf":_hs.idx.get_bm25_idf(term),
        "bm25":    _hs.idx.bm25(doc_id, term),
    }


def chunk_text(text: str, chunk_size: int, mode: str) -> list[str]:
    """Chunk a piece of text using fixed-size or semantic chunking.

    Used by the Chunking Explorer in the Semantic Playground.
    """
    if mode == "fixed":
        return _hs.semantic_search.fixed_size_chunking(text, chunk_size)
    else:
        return _hs.semantic_search.semantic_chunking(text)


def enhance_query(query: str, enhance_type: str) -> str:
    """Rewrite a query using the LLM (spell correction, rewrite, or expansion).

    Why lazy import?
    lib.llm raises RuntimeError at module load time if GEMINI_API_KEY is missing.
    By importing inside this function body, the import only runs when this
    function is actually called — not at server startup.
    """
    from lib.llm import correct_spelling, rewrite_query, expand_query

    if enhance_type == "spell":
        return correct_spelling(query)
    elif enhance_type == "rewrite":
        return rewrite_query(query)
    elif enhance_type == "expand":
        return expand_query(query)
    return query


def rag_answer(query: str, limit: int, mode: str) -> str:
    """Full RAG pipeline: retrieve top docs via RRF, pass to LLM, return answer.

    Lazy import for the same reason as enhance_query.
    """
    from lib.llm import answer_question, rag_summary, cited_summary, question_summary

    # Step 1: retrieve the most relevant documents
    docs = rrf_search(query, limit, k=60)

    # Step 2: pass them to the LLM with the right prompt based on mode
    if mode == "summary":
        return rag_summary(query, docs)
    elif mode == "citation":
        return cited_summary(query, docs)
    elif mode == "question":
        return question_summary(query, docs)
    else:  # default: "answer"
        return answer_question(query, docs)
