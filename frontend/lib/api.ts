import type {
  SearchRequest,
  WeightedSearchRequest,
  RrfSearchRequest,
  RerankRequest,
  RagRequest,
  SearchResponse,
  RagResponse,
} from '@/lib/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`POST ${path} failed (${res.status}): ${text}`)
  }
  return res.json() as Promise<T>
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`GET ${path} failed (${res.status}): ${text}`)
  }
  return res.json() as Promise<T>
}

export const legacySearch = (req: SearchRequest) =>
  post<SearchResponse>('/api/search/keyword', req)

export const bm25Search = (req: SearchRequest) =>
  post<SearchResponse>('/api/search/bm25', req)

export const docSemanticSearch = (req: SearchRequest) =>
  post<SearchResponse>('/api/search/semantic', req)

export const chunkedSemanticSearch = (req: SearchRequest) =>
  post<SearchResponse>('/api/search/semantic/chunked', req)

export const weightedSearch = (req: WeightedSearchRequest) =>
  post<SearchResponse>('/api/search/hybrid/weighted', req)

export const rrfSearch = (req: RrfSearchRequest) =>
  post<SearchResponse>('/api/search/hybrid/rrf', req)

export const batchRerank = (req: RerankRequest) =>
  post<SearchResponse>('/api/search/rerank/batch', req)

export const crossEncoderRerank = (req: RerankRequest) =>
  post<SearchResponse>('/api/search/rerank/cross-encoder', req)

export const ragSearch = (req: RagRequest) =>
  post<RagResponse>('/api/search/rag', req)

export const healthCheck = () =>
  get<{ status: string; indexes_loaded: boolean }>('/api/search/health')
