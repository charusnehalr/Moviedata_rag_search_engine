'use client'

import { useState, useCallback } from 'react'
import { useSearch } from '@/hooks/useSearch'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'

const DEFAULT_QUERY = 'a lonely robot searching for love and belonging'

export default function WeightedChapter() {
  const [alpha, setAlpha] = useState(0.5)
  const { results, loading, error, elapsed, search } = useSearch('weighted', { limit: 5, alpha })

  const handleSearch = useCallback(
    (q: string) => {
      search(q)
    },
    [search]
  )

  return (
    <ChapterCard
      id="weighted"
      num={5}
      icon="⚖️"
      title="Weighted Hybrid Search"
      problem="Semantic search misses exact names ('WALL-E', 'R2-D2'). BM25 misses meaning. Why choose?"
      solution="Blend normalized scores: α × BM25 + (1-α) × Semantic. Slide to tune the balance."
      color="pink"
      elapsed={elapsed ?? undefined}
    >
      {/* Alpha slider */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>← Pure Semantic</span>
          <span className="font-bold text-gray-900">α = {alpha.toFixed(2)}</span>
          <span>Pure BM25 →</span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={alpha}
          onChange={(e) => setAlpha(parseFloat(e.target.value))}
          className="w-full h-2 rounded-full appearance-none cursor-pointer accent-black"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-0.5">
          <span>0.0</span>
          <span>0.5</span>
          <span>1.0</span>
        </div>
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
