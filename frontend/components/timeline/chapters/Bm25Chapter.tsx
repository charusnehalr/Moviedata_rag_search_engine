'use client'

import { useSearch } from '@/hooks/useSearch'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'

const DEFAULT_QUERY = 'a bear on a funny wild adventure'

export default function Bm25Chapter() {
  const { results, loading, error, elapsed, search } = useSearch('bm25', { limit: 5 })

  return (
    <ChapterCard
      id="bm25"
      num={2}
      
      title="BM25 Scoring"
      problem="Keyword search treats all matches equally. 'robot' in a 3-word title = 'robot' in a 500-word epic. Unfair."
      solution="BM25 scores by term rarity (IDF) × frequency (TF), normalized for document length. Short precise matches win."
      color="emerald"
      elapsed={elapsed ?? undefined}
    >
      <SearchBox
        onSearch={search}
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
        <>
          <div className="mt-4 p-3 rounded-xl bg-gray-100 border-2 border-black text-gray-800 text-xs font-medium">
            BM25 scores reflect term rarity × frequency, normalized by document length. Higher score = rarer word appearing more often in a shorter description.
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
