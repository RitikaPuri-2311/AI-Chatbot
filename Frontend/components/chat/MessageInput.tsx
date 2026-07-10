'use client'
import { useState } from 'react'

interface Props {
  onSend: (content: string) => void
  isLoading: boolean
  placeholder?: string
}

export default function MessageInput({
  onSend,
  isLoading,
  placeholder = 'Message AI... (Shift+Enter for new line)',
}: Props) {
  const [value, setValue] = useState('')
  const MAX_CHARS = 1000

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || isLoading || value.length > MAX_CHARS) return
    onSend(trimmed)
    setValue('')
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900 px-6 py-4">
      <div className="max-w-3xl mx-auto">
      <div className="flex items-end gap-3 bg-gray-50 
      dark:bg-gray-800 border border-gray-200 
      dark:border-gray-600 rounded-2xl px-4 py-3 
      shadow-sm focus-within:border-indigo-400 
      transition-all">
          <textarea
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
            placeholder={placeholder}
            className="flex-1 bg-transparent text-sm text-gray-800 
            dark:text-gray-100 resize-none focus:outline-none 
            disabled:opacity-50 placeholder:text-gray-400 
            dark:placeholder:text-gray-500 max-h-40 overflow-y-auto"
            style={{ minHeight: '24px' }}
          />
          <div className="flex items-center gap-2 shrink-0">
            {value.length > 800 && (
              <span className={`text-xs ${
                value.length > MAX_CHARS 
                  ? 'text-red-500' 
                  : 'text-gray-400'
              }`}>
                {value.length}/{MAX_CHARS}
              </span>
            )}
            <button
              onClick={handleSend}
              disabled={isLoading || !value.trim() || 
                value.length > MAX_CHARS}
              className="w-8 h-8 bg-indigo-600 hover:bg-indigo-700 
              disabled:opacity-40 disabled:cursor-not-allowed 
              rounded-lg flex items-center justify-center 
              transition-colors shrink-0"
            >
              <svg xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" fill="currentColor" 
                className="w-4 h-4 text-white">
                <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 
                7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 
                7.905a.75.75 0 00.926.94 60.519 60.519 0 
                0018.445-8.986.75.75 0 000-1.218A60.517 
                60.517 0 003.478 2.405z" />
              </svg>
            </button>
          </div>
        </div>
        <p className="text-xs text-gray-400 text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}