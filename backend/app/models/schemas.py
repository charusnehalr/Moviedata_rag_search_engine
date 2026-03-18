from pydantic import BaseModel


# ─────────────────────────────────────────────
# Building Blocks
# ─────────────────────────────────────────────

class ResultScores(BaseModel):
    bm25: float | None = None
    semantic: float | None = None
    hybrid: float | None = None
    rrf: float | None = None
    rerank: float | None = None   # re-ranking score (batch or cross-encoder)


class ResultRanks(BaseModel):
    bm25_rank: int | None = None
    sem_rank: int | None = None


# ─────────────────────────────────────────────
# Core Result + Response Models
# ─────────────────────────────────────────────

class SearchResult(BaseModel):
    id: str
    title: str
    snippet: str          # first 200 chars of description
    rank: int             # 1-based position in result list
    scores: ResultScores
    ranks: ResultRanks


class SearchResponse(BaseModel):
    query: str
    method: str           # "keyword" | "semantic" | "weighted" | "rrf"
    limit: int
    elapsed_ms: int
    results: list[SearchResult]


class CompareResponse(BaseModel):
    query: str
    limit: int
    elapsed_ms: int
    methods: dict[str, SearchResponse]   # keys: "keyword", "semantic", "weighted", "rrf"


class RagResponse(BaseModel):
    query: str
    enhanced_query: str | None = None
    answer: str
    elapsed_ms: int


# ─────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    enhance: str | None = None   # "spell" | "rewrite" | "expand"


class WeightedSearchRequest(BaseModel):
    query: str
    limit: int = 10
    alpha: float = 0.5
    enhance: str | None = None


class RrfSearchRequest(BaseModel):
    query: str
    limit: int = 10
    k: int = 60
    enhance: str | None = None


class RagRequest(BaseModel):
    query: str
    limit: int = 5
    mode: str = "answer"   # "answer" | "summary" | "citation" | "question"
    enhance: str | None = None


class RerankRequest(BaseModel):
    query: str
    limit: int = 10                      # final results to return after re-ranking
    retrieval_limit: int | None = None   # candidates to retrieve before re-ranking
    # If retrieval_limit is None, it defaults to limit * 5 in the engine
    # (matches the CLI behavior: rrf_limit = limit * 5 if rerank_method else limit)
    # Typical ratio: retrieve 50, return 10 — the re-ranker filters the noise


# ─────────────────────────────────────────────
# Utility Models
# ─────────────────────────────────────────────

class TermScoreRequest(BaseModel):
    doc_id: int
    term: str


class TermScoreResult(BaseModel):
    term: str
    doc_id: int
    tf: float
    idf: float
    tfidf: float
    bm25_tf: float
    bm25_idf: float
    bm25: float


class ChunkRequest(BaseModel):
    text: str
    chunk_size: int = 200
    overlap: int = 1
    mode: str = "fixed"   # "fixed" | "semantic"


class ChunkResult(BaseModel):
    chunks: list[str]
    total_chunks: int
    mode: str
