'use client'

import { useEffect, useRef, useState } from 'react'

interface ScoreBarProps {
  label: string
  value: number
  max: number
  colorClass: string
}

export default function ScoreBar({ label, value, max, colorClass }: ScoreBarProps) {
  const [width, setWidth] = useState(0)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          const pct = Math.min((value / max) * 100, 100)
          setWidth(pct)
          observer.disconnect()
        }
      },
      { threshold: 0.1 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [value, max])

  const displayValue = value < 0.01 ? value.toFixed(4) : value < 1 ? value.toFixed(3) : value.toFixed(1)

  return (
    <div ref={ref} className="flex items-center gap-2 text-xs">
      <span className="w-16 text-gray-500 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${colorClass}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="w-10 text-right text-gray-600 font-mono shrink-0">{displayValue}</span>
    </div>
  )
}
