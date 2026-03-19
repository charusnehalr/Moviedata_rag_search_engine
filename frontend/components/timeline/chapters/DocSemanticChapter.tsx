'use client'

import { useCallback, useState } from 'react'
import { useSearch } from '@/hooks/useSearch'
import ChapterCard from '@/components/timeline/ChapterCard'
import SearchBox from '@/components/shared/SearchBox'
import ResultCard from '@/components/shared/ResultCard'

const DEFAULT_QUERY = 'a bear on a funny wild adventure'

export default function DocSemanticChapter() {
  const bm25 = useSearch('bm25', { limit: 5 })
  const semantic = useSearch('docSemantic', { limit: 5 })
  const [searched, setSearched] = useState(false)

  const handleSearch = useCallback(
    (q: string) => {
      bm25.search(q)
      semantic.search(q)
      setSearched(true)
    },
    [bm25, semantic]
  )

  const loading = bm25.loading || semantic.loading
  const elapsed = semantic.elapsed ?? bm25.elapsed ?? undefined

  return (
    <ChapterCard
      id="docSem"
      num={3}
      
      title="Document Semantic Search"
      problem="BM25 needs exact word matches. Query 'lonely robot' returns nothing if the movie says 'isolated machine'."
      solution="Embeddings map meaning to vectors. Cosine similarity finds movies that mean the same thing, even with zero word overlap."
      color="violet"
      elapsed={elapsed}
    >
      <SearchBox
        onSearch={handleSearch}
        defaultQuery={DEFAULT_QUERY}
        loading={loading}
        colorClass="focus:border-black"
      />

      {(bm25.error || semantic.error) && (
        <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {bm25.error || semantic.error}
        </div>
      )}

      {searched && !loading && (bm25.results.length > 0 || semantic.results.length > 0) && (
        <>
          <div className="mt-4 p-3 rounded-xl bg-gray-100 border-2 border-black text-gray-800 text-xs font-medium">
            &quot;WALL-E&quot; appears in semantic even though the query doesn&apos;t say &quot;WALL-E&quot;, &quot;space&quot;, or &quot;garbage&quot;. Pure meaning match.
          </div>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* BM25 column */}
            <div>
              <h3 className="text-xs font-extrabold text-gray-500 uppercase tracking-wide mb-2">
                BM25 (word matching)
              </h3>
              <div className="space-y-2">
                {bm25.results.length > 0 ? (
                  bm25.results.map((r) => (
                    <ResultCard key={r.id} result={r} rankBg="bg-gray-100" />
                  ))
                ) : (
                  <p className="text-xs text-gray-400 italic p-3">No results — no exact word matches found.</p>
                )}
              </div>
            </div>

            {/* Semantic column */}
            <div>
              <h3 className="text-xs font-extrabold text-gray-500 uppercase tracking-wide mb-2">
                Doc Semantic (meaning matching)
              </h3>
              <div className="space-y-2">
                {semantic.results.length > 0 ? (
                  semantic.results.map((r) => (
                    <ResultCard key={r.id} result={r} rankBg="bg-gray-100" />
                  ))
                ) : (
                  <p className="text-xs text-gray-400 italic p-3">No results.</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </ChapterCard>
  )
}
