'use client'

import { useState, useCallback } from 'react'
import type { SearchResult, SearchMethod } from '@/lib/types'
import * as api from '@/lib/api'

interface UseSearchOptions {
  limit?: number
  alpha?: number
  k?: number
  enhance?: string
  retrievalLimit?: number
}

interface UseSearchReturn {
  query: string
  results: SearchResult[]
  loading: boolean
  error: string | null
  elapsed: number | null
  search: (q: string) => Promise<void>
  reset: () => void
}

export function useSearch(method: SearchMethod, options: UseSearchOptions = {}): UseSearchReturn {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState<number | null>(null)

  const search = useCallback(async (q: string) => {
    if (!q.trim()) return
    setQuery(q)
    setLoading(true)
    setError(null)
    setResults([])
    setElapsed(null)

    try {
      const limit = options.limit ?? 5

      let response

      switch (method) {
        case 'legacy':
          response = await api.legacySearch({ query: q, limit })
          break

        case 'bm25':
          response = await api.bm25Search({ query: q, limit })
          break

        case 'docSemantic':
          response = await api.docSemanticSearch({ query: q, limit })
          break

        case 'chunked':
          response = await api.chunkedSemanticSearch({ query: q, limit })
          break

        case 'weighted':
          response = await api.weightedSearch({
            query: q,
            limit,
            alpha: options.alpha ?? 0.5,
          })
          break

        case 'rrf':
          response = await api.rrfSearch({
            query: q,
            limit,
            k: options.k ?? 60,
            enhance: options.enhance,
          })
          break

        case 'batchRerank':
          response = await api.batchRerank({
            query: q,
            limit,
            retrieval_limit: options.retrievalLimit ?? 25,
          })
          break

        case 'crossEncoder':
          response = await api.crossEncoderRerank({
            query: q,
            limit,
            retrieval_limit: options.retrievalLimit ?? 25,
          })
          break

        default:
          throw new Error(`Unknown search method: ${method}`)
      }

      setResults(response.results)
      setElapsed(response.elapsed_ms)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred')
    } finally {
      setLoading(false)
    }
  }, [method, options.limit, options.alpha, options.k, options.enhance, options.retrievalLimit])

  const reset = useCallback(() => {
    setQuery('')
    setResults([])
    setLoading(false)
    setError(null)
    setElapsed(null)
  }, [])

  return { query, results, loading, error, elapsed, search, reset }
}
