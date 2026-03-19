import TimelineNav from '@/components/timeline/TimelineNav'
import LegacyChapter from '@/components/timeline/chapters/LegacyChapter'
import Bm25Chapter from '@/components/timeline/chapters/Bm25Chapter'
import DocSemanticChapter from '@/components/timeline/chapters/DocSemanticChapter'
import ChunkedChapter from '@/components/timeline/chapters/ChunkedChapter'
import WeightedChapter from '@/components/timeline/chapters/WeightedChapter'
import RrfChapter from '@/components/timeline/chapters/RrfChapter'
import RerankChapter from '@/components/timeline/chapters/RerankChapter'
import RagChapter from '@/components/timeline/chapters/RagChapter'


export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="bg-white border-b-2 border-black py-16 px-4"
        style={{ boxShadow: '0 4px 0px #000' }}>
        <div className="max-w-4xl mx-auto text-center">

          {/* Badge */}
          <div className="inline-block border-2 border-black rounded-full px-4 py-1 text-xs font-bold mb-6 animate-fade-up text-black bg-white"
            style={{ boxShadow: '2px 2px 0px #000' }}>
            8 algorithms · 1 query · live demos
          </div>

          {/* Title */}
          <h1 className="text-5xl sm:text-6xl font-extrabold text-black leading-tight mb-4 animate-fade-up"
            style={{ animationDelay: '0.05s' }}>
            How Search<br />Learned to Think
          </h1>

          {/* Subtitle */}
          <p className="text-gray-500 text-lg max-w-lg mx-auto mb-10 animate-fade-up"
            style={{ animationDelay: '0.1s' }}>
            From counting words → understanding meaning.<br />
            Watch the same query evolve through 8 algorithms.
          </p>

          {/* Scroll hint */}
          <p className="text-gray-400 text-sm font-medium animate-float">↓ scroll to explore</p>
        </div>
      </section>

      {/* Sticky nav */}
      <TimelineNav />

      {/* Chapters */}
      <div className="max-w-4xl mx-auto px-4 pb-4">
        <LegacyChapter />
        <Bm25Chapter />
        <DocSemanticChapter />
        <ChunkedChapter />
        <WeightedChapter />
        <RrfChapter />
        <RerankChapter />
        <RagChapter />
      </div>

      {/* Footer */}
      <footer className="border-t-2 border-black bg-white mt-4 py-8 text-center text-sm text-gray-500">
        <p className="font-bold text-black">RAG Observatory</p>
        <p className="mt-1 text-xs">8 algorithms · one query · Next.js 16 + Tailwind CSS v4</p>
      </footer>
    </main>
  )
}
