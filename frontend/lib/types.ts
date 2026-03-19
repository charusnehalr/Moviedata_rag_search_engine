export interface ResultScores {
  bm25: number | null
  semantic: number | null
  hybrid: number | null
  rrf: number | null
  rerank: number | null
}

export interface ResultRanks {
  bm25_rank: number | null
  sem_rank: number | null
}

export interface SearchResult {
  id: string
  title: string
  snippet: string
  rank: number
  scores: ResultScores
  ranks: ResultRanks
}

export interface SearchResponse {
  query: string
  method: string
  limit: number
  elapsed_ms: number
  results: SearchResult[]
}

export interface RagResponse {
  query: string
  enhanced_query: string | null
  answer: string
  elapsed_ms: number
}

export interface SearchRequest {
  query: string
  limit?: number
  enhance?: string
}

export interface WeightedSearchRequest extends SearchRequest {
  alpha?: number
}

export interface RrfSearchRequest extends SearchRequest {
  k?: number
}

export interface RerankRequest {
  query: string
  limit?: number
  retrieval_limit?: number
}

export interface RagRequest {
  query: string
  limit?: number
  mode?: string
  enhance?: string
}

export type SearchMethod =
  | 'legacy'
  | 'bm25'
  | 'docSemantic'
  | 'chunked'
  | 'weighted'
  | 'rrf'
  | 'batchRerank'
  | 'crossEncoder'

export type ChapterColor =
  | 'amber'
  | 'emerald'
  | 'violet'
  | 'orange'
  | 'pink'
  | 'teal'
  | 'rose'
  | 'purple'
