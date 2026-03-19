'use client'

import { useSearch } from '@/hooks/useSearch'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'

const DEFAULT_QUERY = 'a lonely robot searching for love and belonging'

export default function ChunkedChapter() {
  const { results, loading, error, elapsed, search } = useSearch('chunked', { limit: 5 })

  return (
    <ChapterCard
      id="chunked"
      num={4}
      icon="✂️"
      title="Chunked Semantic Search"
      problem="One embedding per full description. A 10-sentence plot summary gets averaged into one vector — specific details get diluted."
      solution="Split each description into sentence chunks. Each chunk gets its own embedding. The best-matching chunk wins per movie."
      color="orange"
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
            The snippet shown is the winning chunk — the single sentence most similar to your query. Notice how it&apos;s more specific than a full-document match.
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
