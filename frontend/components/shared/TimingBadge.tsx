interface TimingBadgeProps {
  ms: number
}

export default function TimingBadge({ ms }: TimingBadgeProps) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 text-xs font-mono border border-gray-200">
      {Math.round(ms)}ms
    </span>
  )
}
