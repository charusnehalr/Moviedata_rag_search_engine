'use client'

interface LoadingDotsProps {
  colorClass?: string
}

export default function LoadingDots({ colorClass = 'bg-gray-400' }: LoadingDotsProps) {
  return (
    <span className="inline-flex items-center gap-1">
      <span
        className={`inline-block w-2 h-2 rounded-full animate-dot ${colorClass}`}
        style={{ animationDelay: '0s' }}
      />
      <span
        className={`inline-block w-2 h-2 rounded-full animate-dot ${colorClass}`}
        style={{ animationDelay: '0.15s' }}
      />
      <span
        className={`inline-block w-2 h-2 rounded-full animate-dot ${colorClass}`}
        style={{ animationDelay: '0.3s' }}
      />
    </span>
  )
}
