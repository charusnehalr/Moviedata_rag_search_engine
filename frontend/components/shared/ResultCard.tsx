'use client'

import type { SearchResult } from '@/lib/types'
import ScoreBar from './ScoreBar'

interface ResultCardProps {
  result: SearchResult
  rankBg?: string   // kept for compat but unused — B&W only
}

export default function ResultCard({ result }: ResultCardProps) {
  const { scores, ranks } = result

  const hasScores =
    scores.bm25 !== null || scores.semantic !== null ||
    scores.hybrid !== null || scores.rrf !== null || scores.rerank !== null

  const hasRanks = ranks.bm25_rank !== null || ranks.sem_rank !== null

  return (
    <div className="bg-white rounded-xl border-2 border-gray-200 p-3 hover:-translate-y-0.5 hover:border-black transition-all duration-200"
      style={{ boxShadow: '2px 2px 0px #ddd' }}>
      <div className="flex items-start gap-3">
        <span className="shrink-0 w-7 h-7 rounded-full bg-black text-white flex items-center justify-center text-xs font-bold">
          {result.rank}
        </span>
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-gray-900 text-sm leading-snug mb-1 truncate">
            {result.title}
          </h4>
          <p className="text-gray-500 text-xs leading-relaxed line-clamp-2">{result.snippet}</p>

          {hasScores && (
            <div className="mt-3 space-y-1.5">
              {scores.bm25     !== null && <ScoreBar label="BM25"     value={scores.bm25}     max={20}  colorClass="bg-gray-900" />}
              {scores.semantic !== null && <ScoreBar label="Semantic"  value={scores.semantic} max={1}   colorClass="bg-gray-600" />}
              {scores.hybrid   !== null && <ScoreBar label="Hybrid"    value={scores.hybrid}   max={1}   colorClass="bg-gray-800" />}
              {scores.rrf      !== null && <ScoreBar label="RRF"       value={scores.rrf}      max={0.1} colorClass="bg-gray-700" />}
              {scores.rerank   !== null && <ScoreBar label="Rerank"    value={scores.rerank}   max={1}   colorClass="bg-gray-950" />}
            </div>
          )}

          {hasRanks && (
            <div className="mt-2 flex gap-3 text-xs text-gray-400">
              {ranks.bm25_rank !== null && (
                <span>BM25 rank: <span className="font-semibold text-gray-600">#{ranks.bm25_rank}</span></span>
              )}
              {ranks.sem_rank !== null && (
                <span>Sem rank: <span className="font-semibold text-gray-600">#{ranks.sem_rank}</span></span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
