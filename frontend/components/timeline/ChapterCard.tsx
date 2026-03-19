'use client'

import { useEffect, useRef, useState } from 'react'
import TimingBadge from '@/components/shared/TimingBadge'

interface ChapterCardProps {
  id: string
  num: number
  icon?: string
  title: string
  problem: string
  solution: string
  color?: string
  elapsed?: number
  children: React.ReactNode
}

export default function ChapterCard({
  id, num, title, problem, solution, elapsed, children,
}: ChapterCardProps) {
  const sectionRef = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); observer.disconnect() } },
      { threshold: 0.08 }
    )
    if (sectionRef.current) observer.observe(sectionRef.current)
    return () => observer.disconnect()
  }, [])

  return (
    <section ref={sectionRef} id={id} className="scroll-mt-20 py-8">
      <div className={`flex gap-5 transition-all duration-700 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>

        {/* Left: timeline line + node */}
        <div className="flex flex-col items-center shrink-0">
          <div className="w-10 h-10 rounded-full bg-white border-2 border-black text-black flex items-center justify-center text-sm font-extrabold z-10 shrink-0"
            style={{ boxShadow: '2px 2px 0px #000' }}>
            {num}
          </div>
          <div className="flex-1 w-0 border-l-2 border-dashed border-gray-300 mt-2" />
        </div>

        {/* Right: card */}
        <div
          className="flex-1 bg-white border-2 border-black rounded-2xl p-6 min-w-0"
          style={{ boxShadow: '5px 5px 0px #000' }}
        >
          {/* Header */}
          <div className="flex items-center gap-3 mb-4 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-extrabold border-2 border-black text-black bg-white">
              #{num}
            </span>
            <h2 className="text-2xl font-extrabold text-gray-900 flex-1">{title}</h2>
            {elapsed !== undefined && elapsed > 0 && <TimingBadge ms={elapsed} />}
          </div>

          {/* Problem + Solution */}
          <div className="mb-5 space-y-2">
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-16 mt-0.5 px-1.5 py-0.5 text-[10px] font-extrabold uppercase tracking-widest border border-red-600 rounded text-red-700 text-center">
                problem
              </span>
              <p className="text-sm text-gray-500 italic leading-relaxed">{problem}</p>
            </div>
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-16 mt-0.5 px-1.5 py-0.5 text-[10px] font-extrabold uppercase tracking-widest border border-emerald-700 text-emerald-800 rounded text-center">
                fix
              </span>
              <p className="text-sm font-semibold text-gray-900 leading-relaxed">{solution}</p>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-gray-200 mb-5" />

          {children}
        </div>
      </div>
    </section>
  )
}
