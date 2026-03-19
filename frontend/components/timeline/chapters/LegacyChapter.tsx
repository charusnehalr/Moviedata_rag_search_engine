'use client'

import { useSearch } from '@/hooks/useSearch'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'

const DEFAULT_QUERY = 'a bear on a funny wild adventure'

export default function LegacyChapter() {
  const { results, loading, error, elapsed, search } = useSearch('legacy', { limit: 5 })

  return (
    <ChapterCard
      id="legacy"
      num={1}
      icon="🔤"
      title="Legacy Keyword Search"
      problem="Every word searched literally. 'loves' won't match 'love'. No ranking — results appear in random index order."
      solution="Inverted index maps every token to its documents. The foundation all search is built on."
      color="amber"
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
            No scoring — these results could be in any order. Try: search &quot;robot&quot; vs &quot;robots&quot; and see different results.
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
