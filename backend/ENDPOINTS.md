# RAG Observatory — API Endpoint Reference

Base URL: `http://localhost:8000`

---

## Health Check

### GET `/api/search/health`
Check that the server is up and indexes are loaded.

**Response**
```json
{
  "status": "ok",
  "indexes_loaded": true
}
```

**curl (Windows cmd)**
```cmd
curl http://localhost:8000/api/search/health
```

---

## Search Endpoints

All search endpoints accept an optional `enhance` field:
- `"spell"` — correct spelling in the query before searching
- `"rewrite"` — rephrase the query for better retrieval
- `"expand"` — add related terms to the query

---

### POST `/api/search/keyword`
BM25 keyword search. Finds documents containing your exact words.

**Request body**
```json
{
  "query": "man stranded alone on hostile planet",
  "limit": 5,
  "enhance": null
}
```

**Response**
```json
{
  "query": "man stranded alone on hostile planet",
  "method": "keyword",
  "limit": 5,
  "elapsed_ms": 45,
  "results": [
    {
      "id": "tt0369610",
      "title": "The Martian",
      "snippet": "An astronaut becomes stranded on Mars...",
      "rank": 1,
      "scores": { "bm25": 12.6, "semantic": null, "hybrid": null, "rrf": null },
      "ranks": { "bm25_rank": null, "sem_rank": null }
    }
  ]
}
```

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/keyword -H "Content-Type: application/json" -d "{\"query\": \"man stranded alone on hostile planet\", \"limit\": 5}"
```

---

### POST `/api/search/semantic`
Chunked semantic search using sentence embeddings. Finds documents by meaning, not just words.

**Request body**
```json
{
  "query": "man stranded alone on hostile planet",
  "limit": 5,
  "enhance": null
}
```

**Response** — same shape as keyword, but `scores.semantic` is filled (cosine similarity 0–1), `scores.bm25` is null.

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/semantic -H "Content-Type: application/json" -d "{\"query\": \"man stranded alone on hostile planet\", \"limit\": 5}"
```

---

### POST `/api/search/hybrid/weighted`
Weighted hybrid: blends normalized BM25 + semantic scores using `alpha`.

**Request body**
```json
{
  "query": "man stranded alone on hostile planet",
  "limit": 5,
  "alpha": 0.5,
  "enhance": null
}
```

| alpha | Effect |
|-------|--------|
| `1.0` | Pure BM25 |
| `0.5` | Equal blend (default) |
| `0.0` | Pure semantic |

**Response** — `scores.bm25`, `scores.semantic`, and `scores.hybrid` are all filled.

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/hybrid/weighted -H "Content-Type: application/json" -d "{\"query\": \"man stranded alone on hostile planet\", \"limit\": 5, \"alpha\": 0.3}"
```

---

### POST `/api/search/hybrid/rrf`
Reciprocal Rank Fusion: fuses BM25 and semantic rank positions.
Formula: `RRF(doc) = 1/(bm25_rank + k) + 1/(sem_rank + k)`

**Request body**
```json
{
  "query": "man stranded alone on hostile planet",
  "limit": 5,
  "k": 60,
  "enhance": null
}
```

| k | Effect |
|---|--------|
| Low (1–10) | Top-ranked docs dominate |
| High (60+) | Rank differences matter less (smoother fusion) |

**Response** — `scores.rrf` is filled, `ranks.bm25_rank` and `ranks.sem_rank` show each method's original position.

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/hybrid/rrf -H "Content-Type: application/json" -d "{\"query\": \"man stranded alone on hostile planet\", \"limit\": 5, \"k\": 60}"
```

---

### POST `/api/search/compare`
Runs all 4 methods in parallel. Returns results from keyword, semantic, weighted, and RRF in one response.

**Request body**
```json
{
  "query": "man stranded alone on hostile planet",
  "limit": 5
}
```

**Response**
```json
{
  "query": "man stranded alone on hostile planet",
  "limit": 5,
  "elapsed_ms": 430,
  "methods": {
    "keyword":  { "method": "keyword",  "results": [...] },
    "semantic": { "method": "semantic", "results": [...] },
    "weighted": { "method": "weighted", "results": [...] },
    "rrf":      { "method": "rrf",      "results": [...] }
  }
}
```

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/compare -H "Content-Type: application/json" -d "{\"query\": \"man stranded alone on hostile planet\", \"limit\": 5}"
```

---

### POST `/api/search/rag`
Full RAG pipeline: retrieves top docs via RRF, passes them to Gemini LLM, returns a generated answer.

**Request body**
```json
{
  "query": "man stranded alone on hostile planet",
  "limit": 5,
  "mode": "answer",
  "enhance": null
}
```

| mode | Output |
|------|--------|
| `"answer"` | Direct answer to the query |
| `"summary"` | Summary of the retrieved documents |
| `"citation"` | Answer with [1][2] citations |
| `"question"` | Q&A format — generates follow-up questions and answers |

**Response**
```json
{
  "query": "man stranded alone on hostile planet",
  "enhanced_query": null,
  "answer": "Based on the retrieved movies, the best match is The Martian (2015)...",
  "elapsed_ms": 1800
}
```

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/rag -H "Content-Type: application/json" -d "{\"query\": \"man stranded alone on hostile planet\", \"limit\": 5, \"mode\": \"answer\"}"
```

---

## Utility Endpoints

### POST `/api/search/scores/term`
Returns TF, IDF, TF-IDF, BM25-TF, BM25-IDF, BM25 for a single term in a single document.
Used by the Score Explorer panel in the Keyword Playground.

**Request body**
```json
{
  "doc_id": 123,
  "term": "stranded"
}
```

**Response**
```json
{
  "term": "stranded",
  "doc_id": 123,
  "tf": 2,
  "idf": 3.21,
  "tfidf": 6.42,
  "bm25_tf": 1.71,
  "bm25_idf": 2.63,
  "bm25": 4.50
}
```

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/scores/term -H "Content-Type: application/json" -d "{\"doc_id\": 123, \"term\": \"stranded\"}"
```

---

### POST `/api/search/chunk`
Chunks a piece of text and returns the resulting chunks.
Used by the Chunking Explorer in the Semantic Playground.

**Request body**
```json
{
  "text": "An astronaut becomes stranded on Mars after his team abandons the mission...",
  "chunk_size": 200,
  "overlap": 1,
  "mode": "fixed"
}
```

| mode | Behavior |
|------|----------|
| `"fixed"` | Splits by word count (`chunk_size` words per chunk) |
| `"semantic"` | Splits on sentence boundaries |

**Response**
```json
{
  "chunks": [
    "An astronaut becomes stranded on Mars after his team...",
    "...abandons the mission believing him dead."
  ],
  "total_chunks": 2,
  "mode": "fixed"
}
```

**curl (Windows cmd)**
```cmd
curl -X POST http://localhost:8000/api/search/chunk -H "Content-Type: application/json" -d "{\"text\": \"An astronaut becomes stranded on Mars.\", \"mode\": \"fixed\"}"
```

---

## Interactive API Docs

FastAPI auto-generates interactive docs from your schemas.
Open in browser after starting the server:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These pages let you test every endpoint directly in the browser — no curl needed.
