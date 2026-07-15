'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Loader2, Paperclip } from 'lucide-react'
import toast from 'react-hot-toast'

interface Props {
  onSend: (content: string) => void
  isLoading: boolean
  placeholder?: string
  showAttach?: boolean
}

export default function MessageInput({
  onSend,
  isLoading,
  placeholder = 'Message AI...',
  showAttach = true,
}: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const MAX_CHARS = 1000

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [])

  useEffect(() => {
    adjustHeight()
  }, [value, adjustHeight])

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || isLoading || value.length > MAX_CHARS) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleAttach() {
    toast('Document attachment coming soon', { icon: '📎' })
  }

  return (
    <div className="shrink-0 border-t border-[var(--color-border-subtle)]
      bg-[var(--color-surface)] px-4 py-4">
      <div className="max-w-3xl mx-auto">
        <div
          className="flex items-end gap-2 bg-[var(--color-surface-raised)]
            border border-[var(--color-border-subtle)] rounded-2xl px-3 py-2.5
            shadow-sm focus-within:border-violet-500/40
            focus-within:shadow-violet-900/10 transition-all duration-200"
        >
          {showAttach && (
            <button
              type="button"
              onClick={handleAttach}
              disabled={isLoading}
              aria-label="Attach document"
              className="p-2 rounded-xl text-[var(--color-text-muted)]
                hover:text-violet-400 hover:bg-violet-600/10
                disabled:opacity-40 transition-all shrink-0 mb-0.5"
            >
              <Paperclip className="w-4 h-4" />
            </button>
          )}

          <textarea
            ref={textareaRef}
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
            placeholder={placeholder}
            aria-label="Message input"
            className="flex-1 bg-transparent text-sm text-[var(--color-text-primary)]
              resize-none focus:outline-none disabled:opacity-50
              placeholder:text-[var(--color-text-muted)] overflow-y-auto
              leading-relaxed py-1.5"
          />

          <div className="flex items-center gap-2 shrink-0 mb-0.5">
            {value.length > 800 && (
              <span
                className={`text-[10px] tabular-nums ${
                  value.length > MAX_CHARS ? 'text-red-400' : 'text-[var(--color-text-muted)]'
                }`}
                aria-live="polite"
              >
                {value.length}/{MAX_CHARS}
              </span>
            )}
            <button
              type="button"
              onClick={handleSend}
              disabled={isLoading || !value.trim() || value.length > MAX_CHARS}
              aria-label={isLoading ? 'Generating response' : 'Send message'}
              className="w-9 h-9 bg-gradient-to-br from-violet-600 to-indigo-600
                hover:from-violet-500 hover:to-indigo-500
                disabled:opacity-30 disabled:cursor-not-allowed
                rounded-xl flex items-center justify-center
                transition-all duration-200 shadow-sm shadow-violet-900/20"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 text-white animate-spin" />
              ) : (
                <Send className="w-4 h-4 text-white" />
              )}
            </button>
          </div>
        </div>
        <p className="text-[10px] text-[var(--color-text-muted)] text-center mt-2">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
