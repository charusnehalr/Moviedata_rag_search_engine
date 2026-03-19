'use client'

import { useState, useCallback } from 'react'
import { useSearch } from '@/hooks/useSearch'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'

const DEFAULT_QUERY = 'a lonely robot searching for love and belonging'

const ENHANCE_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'spell', label: 'Spell Correct' },
  { value: 'rewrite', label: 'Rewrite' },
  { value: 'expand', label: 'Expand' },
]

export default function RrfChapter() {
  const [enhance, setEnhance] = useState<string | undefined>(undefined)
  const { results, loading, error, elapsed, search } = useSearch('rrf', {
    limit: 5,
    k: 60,
    enhance,
  })

  const handleSearch = useCallback(
    (q: string) => {
      search(q)
    },
    [search]
  )

  return (
    <ChapterCard
      id="rrf"
      num={6}
      icon="🏆"
      title="Reciprocal Rank Fusion (RRF)"
      problem="Score normalization is fragile — BM25 and semantic live on different scales. A BM25 score of 12 vs semantic 0.8 — incomparable."
      solution="Ignore scores. Fuse rank positions: 1/(BM25_rank + 60) + 1/(Sem_rank + 60). Robust, no normalization needed."
      color="teal"
      elapsed={elapsed ?? undefined}
    >
      {/* Enhance dropdown */}
      <div className="mb-4 flex items-center gap-3">
        <label className="text-xs font-bold text-gray-700 shrink-0">Query Enhancement:</label>
        <select
          value={enhance ?? ''}
          onChange={(e) => setEnhance(e.target.value || undefined)}
          className="px-3 py-1.5 rounded-xl border-2 border-gray-300 bg-white text-sm font-medium text-gray-700 outline-none focus:border-black cursor-pointer"
        >
          {ENHANCE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {enhance && (
          <span className="text-xs text-gray-500 italic">
            ✨ Query will be rewritten by LLM before searching
          </span>
        )}
      </div>

      <SearchBox
        onSearch={handleSearch}
        defaultQuery={DEFAULT_QUERY}
        loading={loading}
        colorClass="focus:border-black"
      />

      {error && (
        <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-3 space-y-2">
          {results.map((r) => (
            <ResultCard key={r.id} result={r} />
          ))}
        </div>
      )}
    </ChapterCard>
  )
}
