'use client'

import { useState, type FormEvent } from 'react'
import LoadingDots from './LoadingDots'

interface SearchBoxProps {
  onSearch: (query: string) => void
  defaultQuery?: string
  loading?: boolean
  colorClass?: string
}

export default function SearchBox({
  onSearch,
  defaultQuery = '',
  loading = false,
  colorClass = 'focus:border-gray-400',
}: SearchBoxProps) {
  const [value, setValue] = useState(defaultQuery)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (value.trim() && !loading) {
      onSearch(value.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Enter your search query..."
        disabled={loading}
        className={`flex-1 px-4 py-2.5 rounded-xl border-2 border-gray-200 bg-white text-gray-800 placeholder-gray-400 text-sm font-medium outline-none transition-colors duration-200 ${colorClass} disabled:opacity-60`}
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="px-5 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-bold shrink-0 hover:-translate-y-0.5 hover:shadow-md transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:translate-y-0 disabled:shadow-none flex items-center gap-2"
      >
        {loading ? (
          <>
            <LoadingDots colorClass="bg-white" />
          </>
        ) : (
          'Search'
        )}
      </button>
    </form>
  )
}
