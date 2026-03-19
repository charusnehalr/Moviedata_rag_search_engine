# RAG Observatory

A full-stack search engine that walks through 8 search strategies — from basic keyword matching to Retrieval-Augmented Generation — side by side, on the same dataset. Built as an educational tool to understand how modern search works under the hood.

---

## What it does

The frontend is a scrollable timeline of 8 chapters. Each chapter runs a different search algorithm on a 5,000-movie dataset, shows the results, and explains the problem it solves and how it works.

| # | Chapter | What it demonstrates |
|---|---------|----------------------|
| 1 | Legacy Keyword Search | Inverted index, exact word matching, no ranking |
| 2 | BM25 | Ranked keyword search using term frequency and document length |
| 3 | Document Semantic Search | Whole-document embeddings, cosine similarity |
| 4 | Chunked Semantic Search | Sentence-level embeddings, best-chunk-wins |
| 5 | Weighted Hybrid | BM25 + semantic score blended with a tunable alpha |
| 6 | RRF Hybrid | Reciprocal Rank Fusion — fuses rank positions, no score normalization needed |
| 7 | Neural Reranking | Two-stage: RRF retrieves candidates, then a cross-encoder or LLM reranks |
| 8 | RAG | Retrieve → Augment → Generate: LLM answers using retrieved movie context |

---

## Screenshots

**Hero / Landing**
![Hero](docs/screenshots/hero.png)

**Timeline Overview**
![Timeline](docs/screenshots/timeline.png)

**BM25 Search**
![BM25](docs/screenshots/bm25.png)

**Document Semantic vs BM25 Side-by-side**
![Doc Semantic](docs/screenshots/doc-semantic.png)

**RRF Hybrid Search**
![RRF](docs/screenshots/rrf.png)

**Neural Reranking**
![Reranking](docs/screenshots/reranking.png)

**RAG Answer**
![RAG](docs/screenshots/rag.png)

---

## Tech stack

**Backend**
- Python 3.13+
- FastAPI + Uvicorn
- `sentence-transformers` — semantic embeddings (`all-MiniLM-L6-v2`)
- `nltk` — tokenization, stopwords, stemming
- Google Gemini API — query enhancement, batch reranking, RAG answers
- `uv` — package manager

**Frontend**
- Next.js 16 (App Router)
- React 19
- Tailwind CSS v4
- TypeScript

---

## Project structure

```
rag-search-engine/
├── backend/
│   └── app/
│       ├── main.py                       # FastAPI app, CORS, lifespan
│       ├── routers/search.py             # All /api/search/* endpoints
│       ├── services/engine.py            # Search engine singleton
│       ├── services/response_builder.py  # Normalize raw results to API shape
│       └── models/schemas.py             # Pydantic request/response models
├── cli/
│   └── lib/
│       ├── keyword_search.py             # Inverted index, BM25
│       ├── semantic_search.py            # Document-level embeddings
│       ├── hybrid_search.py              # Chunked semantic, weighted, RRF
│       └── search_utils.py              # Shared utilities, load_movies()
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx                      # Hero + timeline
│   ├── components/
│   │   ├── timeline/
│   │   │   ├── ChapterCard.tsx
│   │   │   ├── TimelineNav.tsx
│   │   │   └── chapters/                 # One file per search chapter
│   │   └── shared/                       # SearchBox, ResultCard, ScoreBar, etc.
│   ├── hooks/useSearch.ts                # Calls API, manages loading/error/results
│   └── lib/
│       ├── api.ts                        # Fetch wrappers for all 9 endpoints
│       └── types.ts                      # Shared TypeScript types
├── data/
│   ├── movies.json                       # 5,000 movies (id, title, description)
│   └── golden_dataset.json               # Evaluation benchmark queries
├── cache/                                # Auto-generated index + embedding files
└── .env                                  # API keys (not committed)
```

---

## Setup

### Prerequisites

- Python 3.13+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) package manager
- A Google Gemini API key (needed for RAG, query enhancement, and batch reranking)

### 1. Clone and install

```bash
git clone <repo-url>
cd rag-search-engine
uv sync
```

### 2. Set environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_key_here
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Running

Open two terminals from the project root.

**Terminal 1 — Backend:**
```bash
uv run uvicorn backend.app.main:app --reload
```

The first startup takes ~30 seconds to load embeddings. On subsequent starts the cache is reused and it loads faster.

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## API endpoints

All endpoints accept POST with a JSON body. Base URL: `http://localhost:8000`

| Endpoint | Body | Description |
|----------|------|-------------|
| `POST /api/search/keyword` | `{query, limit}` | Inverted index keyword search |
| `POST /api/search/bm25` | `{query, limit}` | BM25 ranked keyword search |
| `POST /api/search/semantic` | `{query, limit}` | Document-level semantic search |
| `POST /api/search/semantic/chunked` | `{query, limit}` | Chunked semantic search |
| `POST /api/search/hybrid/weighted` | `{query, limit, alpha}` | Weighted hybrid (BM25 + semantic) |
| `POST /api/search/hybrid/rrf` | `{query, limit, k}` | Reciprocal Rank Fusion hybrid |
| `POST /api/search/rerank/batch` | `{query, limit, retrieval_limit}` | RRF + Gemini LLM reranking |
| `POST /api/search/rerank/cross-encoder` | `{query, limit, retrieval_limit}` | RRF + cross-encoder reranking |
| `POST /api/search/rag` | `{query, limit, mode}` | Full RAG pipeline |
| `GET /api/search/health` | — | Health check |

**RAG modes:** `answer` / `summary` / `citation` / `question`

**Example (Windows CMD):**
```cmd
curl -X POST http://localhost:8000/api/search/bm25 -H "Content-Type: application/json" -d "{\"query\": \"bear adventure\", \"limit\": 5}"
```

---

## How the search pipeline works

```
Query
  │
  ├─ Keyword / BM25 ──────────────────────── Inverted index (exact tokens)
  │
  ├─ Semantic (doc) ──────────────────────── One embedding per movie
  │
  ├─ Semantic (chunked) ──────────────────── One embedding per sentence chunk
  │
  ├─ Hybrid Weighted ─── BM25 + Semantic ─── Normalize scores, blend with alpha
  │
  ├─ Hybrid RRF ──────── BM25 + Semantic ─── Fuse by rank position, no normalization
  │
  ├─ Rerank ──────────── RRF candidates ───── Re-score with cross-encoder or LLM
  │
  └─ RAG ─────────────── RRF retrieval ────── Feed context to Gemini, get answer
```

---

## Cache files

On first run the backend builds and saves index files to `cache/`:

| File | Contents |
|------|----------|
| `cache/index.pkl` | BM25 inverted index |
| `cache/docmap.pkl` | Document ID to movie dict |
| `cache/term_frequencies.pkl` | Per-document term frequencies |
| `cache/doc_lengths.pkl` | Document length stats |
| `cache/chunk_embeddings.npy` | Sentence chunk embeddings |
| `cache/doc_embeddings.npy` | Whole-document embeddings |

Delete `cache/` to force a full rebuild.
