'use client'

import { useEffect, useState } from 'react'

const CHAPTERS = [
  { id: 'legacy',   label: 'Legacy',       num: 1 },
  { id: 'bm25',     label: 'BM25',         num: 2 },
  { id: 'docSem',   label: 'Doc Semantic', num: 3 },
  { id: 'chunked',  label: 'Chunked',      num: 4 },
  { id: 'weighted', label: 'Weighted',     num: 5 },
  { id: 'rrf',      label: 'RRF',          num: 6 },
  { id: 'rerank',   label: 'Reranking',    num: 7 },
  { id: 'rag',      label: 'RAG',          num: 8 },
]

export default function TimelineNav() {
  const [activeId, setActiveId] = useState<string>('legacy')

  useEffect(() => {
    // rootMargin creates a detection band: ignore top 20% and bottom 60% of viewport.
    // A section becomes active the moment it crosses into the middle 20% strip.
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveId(entry.target.id)
        })
      },
      { rootMargin: '-20% 0px -60% 0px', threshold: 0 }
    )

    CHAPTERS.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    })

    return () => observer.disconnect()
  }, [])

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <nav className="sticky top-0 z-40 bg-white border-b-2 border-black" style={{ boxShadow: '0 3px 0px #000' }}>
      <div className="max-w-4xl mx-auto px-4 py-2">
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {CHAPTERS.map((ch) => {
            const isActive = activeId === ch.id
            return (
              <button
                key={ch.id}
                onClick={() => scrollTo(ch.id)}
                className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all duration-200 border-2 ${
                  isActive
                    ? 'bg-black text-white border-black'
                    : 'bg-white text-gray-600 border-gray-300 hover:border-gray-500 hover:text-black'
                }`}
              >
                <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-extrabold ${
                  isActive ? 'bg-white text-black' : 'bg-gray-200 text-gray-600'
                }`}>
                  {ch.num}
                </span>
                {ch.label}
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
