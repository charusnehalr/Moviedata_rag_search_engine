'use client'

import { useState, useCallback } from 'react'
import { useSearch } from '@/hooks/useSearch'
import * as api from '@/lib/api'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'
import LoadingDots from '@/components/shared/LoadingDots'

const DEFAULT_QUERY = 'a bear on a funny wild adventure'

type RagMode = 'answer' | 'summary' | 'citation' | 'question'

const MODES: { value: RagMode; label: string }[] = [
  { value: 'answer', label: 'answer' },
  { value: 'summary', label: 'summary' },
  { value: 'citation', label: 'citation' },
  { value: 'question', label: 'question' },
]

export default function RagChapter() {
  const [mode, setMode] = useState<RagMode>('answer')
  const [answer, setAnswer] = useState<string>('')
  const [answerLoading, setAnswerLoading] = useState(false)
  const [answerError, setAnswerError] = useState<string | null>(null)
  const [enhancedQuery, setEnhancedQuery] = useState<string | null>(null)
  const [ragElapsed, setRagElapsed] = useState<number | null>(null)
  const [searched, setSearched] = useState(false)

  const { results, loading: rrfLoading, error: rrfError, search: rrfSearch } = useSearch('rrf', {
    limit: 5,
  })

  const handleSearch = useCallback(
    async (q: string) => {
      setSearched(true)
      setAnswer('')
      setAnswerError(null)
      setEnhancedQuery(null)
      setRagElapsed(null)

      // Trigger both in parallel
      rrfSearch(q)

      setAnswerLoading(true)
      try {
        const ragResult = await api.ragSearch({ query: q, limit: 5, mode })
        setAnswer(ragResult.answer)
        setEnhancedQuery(ragResult.enhanced_query)
        setRagElapsed(ragResult.elapsed_ms)
      } catch (err) {
        setAnswerError(err instanceof Error ? err.message : 'Failed to generate answer')
      } finally {
        setAnswerLoading(false)
      }
    },
    [rrfSearch, mode]
  )

  const loading = rrfLoading || answerLoading

  return (
    <ChapterCard
      id="rag"
      num={8}
      icon="✨"
      title="Retrieval-Augmented Generation (RAG)"
      problem="Even perfect ranking gives you a list. Users want an answer, not 10 blue links."
      solution="Retrieve top docs via RRF, inject as context, ask LLM to generate a direct answer. Retrieval-Augmented Generation."
      color="purple"
      elapsed={ragElapsed ?? undefined}
    >
      {/* Mode tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        {MODES.map((m) => (
          <button
            key={m.value}
            onClick={() => setMode(m.value)}
            className={`px-3 py-1 rounded-full text-xs font-bold border-2 transition-all duration-200 ${
              mode === m.value
                ? 'bg-black border-black text-white'
                : 'bg-white border-gray-300 text-gray-600 hover:border-black'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      <SearchBox
        onSearch={handleSearch}
        defaultQuery={DEFAULT_QUERY}
        loading={loading}
        colorClass="focus:border-black"
      />

      {rrfError && (
        <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          Search error: {rrfError}
        </div>
      )}

      {searched && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Left: Retrieved Context */}
          <div>
            <h3 className="text-xs font-extrabold text-gray-500 uppercase tracking-wide mb-2">
              Retrieved Context
            </h3>
            {rrfLoading ? (
              <div className="flex items-center gap-2 text-gray-500 text-sm py-4">
                <LoadingDots colorClass="bg-gray-700" />
                <span>Retrieving documents…</span>
              </div>
            ) : results.length > 0 ? (
              <div className="space-y-2">
                {results.map((r) => (
                  <ResultCard key={r.id} result={r} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400 italic p-3">No results retrieved.</p>
            )}
          </div>

          {/* Right: Generated Answer */}
          <div>
            <h3 className="text-xs font-extrabold text-gray-500 uppercase tracking-wide mb-2">
              Generated Answer
              {ragElapsed && (
                <span className="ml-2 font-mono font-normal text-gray-400">
                  ({Math.round(ragElapsed)}ms)
                </span>
              )}
            </h3>
            <div
              className="rounded-2xl border-2 border-black bg-gray-50 p-4 min-h-24"
              style={{ boxShadow: '3px 3px 0px #000' }}
            >
              {answerLoading ? (
                <div className="flex flex-col items-center justify-center py-6 gap-3">
                  <LoadingDots colorClass="bg-gray-700" />
                  <p className="text-xs text-gray-500 font-medium">
                    Generating {mode} with Gemini…
                  </p>
                </div>
              ) : answerError ? (
                <p className="text-red-600 text-sm">{answerError}</p>
              ) : answer ? (
                <>
                  {enhancedQuery && (
                    <p className="text-xs text-gray-400 mb-2 italic">
                      Enhanced query: &quot;{enhancedQuery}&quot;
                    </p>
                  )}
                  <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {answer}
                  </p>
                </>
              ) : (
                <p className="text-xs text-gray-400 italic">Answer will appear here…</p>
              )}
            </div>
          </div>
        </div>
      )}
    </ChapterCard>
  )
}
