'use client'

import { useState, useCallback } from 'react'
import { useSearch } from '@/hooks/useSearch'
import type { SearchMethod } from '@/lib/types'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'
import LoadingDots from '@/components/shared/LoadingDots'

const DEFAULT_QUERY = 'a bear on a funny wild adventure'

export default function RerankChapter() {
  const [mode, setMode] = useState<'crossEncoder' | 'batchRerank'>('crossEncoder')

  const { results, loading, error, elapsed, search, reset } = useSearch(mode as SearchMethod, {
    limit: 5,
    retrievalLimit: 25,
  })

  const handleModeSwitch = useCallback(
    (newMode: 'crossEncoder' | 'batchRerank') => {
      if (newMode !== mode) {
        setMode(newMode)
        reset()
      }
    },
    [mode, reset]
  )

  const handleSearch = useCallback(
    (q: string) => {
      search(q)
    },
    [search]
  )

  return (
    <ChapterCard
      id="rerank"
      num={7}
      
      title="Neural Reranking"
      problem="Fast retrieval (RRF) gets ~50 candidates quickly but imprecisely. The top result might not be the best match."
      solution="Two-stage: retrieve broadly with RRF, then re-score with a heavy model. Stage 2 reorders based on deep (query, document) understanding."
      color="rose"
      elapsed={elapsed ?? undefined}
    >
      {/* Mode toggle */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <button
          onClick={() => handleModeSwitch('crossEncoder')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 text-sm font-bold transition-all duration-200 ${
            mode === 'crossEncoder'
              ? 'bg-black border-black text-white'
              : 'bg-white border-gray-300 text-gray-700 hover:border-black'
          }`}
        >
          Cross-Encoder (TinyBERT)
        </button>
        <button
          onClick={() => handleModeSwitch('batchRerank')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 text-sm font-bold transition-all duration-200 ${
            mode === 'batchRerank'
              ? 'bg-black border-black text-white'
              : 'bg-white border-gray-300 text-gray-700 hover:border-black'
          }`}
        >
          Batch Rerank (Gemini LLM)
        </button>
      </div>

      <p className="text-xs text-gray-500 mb-4">
        {mode === 'crossEncoder'
          ? 'Scores each (query, doc) pair together. Most accurate. ~2-3s.'
          : 'One LLM call ranks all candidates. Understands nuance. ~3-5s.'}
      </p>

      <SearchBox
        onSearch={handleSearch}
        defaultQuery={DEFAULT_QUERY}
        loading={loading}
        colorClass="focus:border-black"
      />

      {loading && (
        <div className="mt-4 flex items-center gap-2 text-gray-600 text-sm">
          <LoadingDots colorClass="bg-gray-700" />
          <span className="font-medium">
            {mode === 'crossEncoder' ? 'Running TinyBERT reranking…' : 'Asking Gemini to rerank…'}
          </span>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <>
          <div className="mt-4 p-3 rounded-xl bg-gray-100 border-2 border-black text-gray-800 text-xs font-medium">
            Both methods first retrieve 25 candidates via RRF, then re-rank them. The final top 5 shown here.
          </div>
          <div className="mt-3 space-y-2">
            {results.map((r) => (
              <ResultCard key={r.id} result={r} />
            ))}
          </div>
        </>
      )}
    </ChapterCard>
  )
}
