'use client'
import { useState } from 'react'

interface Props {
  onSend: (content: string) => void
  isLoading: boolean
}

export default function MessageInput({ onSend, isLoading }: Props) {
  const [value, setValue] = useState('')
  const MAX_CHARS = 1000

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setValue('')
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      <div className="flex gap-3 items-end">
        <div className="flex-1 flex flex-col gap-1">
          <textarea
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={3}
            placeholder="Type a message... (Enter to send)"
            className="w-full border border-gray-300 rounded-xl px-4 py-3 
            text-sm resize-none focus:outline-none focus:ring-2 
            focus:ring-indigo-500 disabled:opacity-50 
            disabled:cursor-not-allowed"
          />
          <span className={`text-xs text-right ${
            value.length > MAX_CHARS 
              ? 'text-red-500' 
              : 'text-gray-400'
          }`}>
            {value.length}/{MAX_CHARS}
          </span>
        </div>
        <button
          onClick={handleSend}
          disabled={isLoading || !value.trim() || value.length > MAX_CHARS}
          className="bg-indigo-600 text-white px-5 py-3 rounded-xl 
          text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 
          disabled:cursor-not-allowed transition-colors mb-5"
        >
          {isLoading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}