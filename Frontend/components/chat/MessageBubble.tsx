'use client'

import { useState } from 'react'
import { Copy, Check, RotateCcw, ThumbsUp, ThumbsDown } from 'lucide-react'
import type { Role, Source } from '@/types'
import ReactMarkdown from 'react-markdown'
import SourcePanel from '@/components/documents/SourcePanel'
import { stripEmbeddedCitations } from '@/lib/citations'
import { formatMessageTime } from '@/lib/formatTime'

interface Props {
  role: Role
  content: string
  createdAt?: string
  sources?: Source[]
  isStreaming?: boolean
  isLastAssistant?: boolean
  onRegenerate?: () => void
}

export default function MessageBubble({
  role,
  content,
  createdAt,
  sources,
  isStreaming = false,
  isLastAssistant = false,
  onRegenerate,
}: Props) {
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
  const isUser = role === 'user'
  const hasSources = Boolean(sources && sources.length > 0)
  const displayContent = hasSources ? stripEmbeddedCitations(content) : content

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(displayContent)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard unavailable
    }
  }

  if (!content && !isStreaming) return null

  return (
    <article
      className={`group flex gap-3 items-start animate-fade-in
        ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      aria-label={isUser ? 'Your message' : 'Assistant message'}
    >
      <div
        className={`w-8 h-8 rounded-2xl flex items-center justify-center
          text-[10px] font-bold shrink-0 mt-0.5
          ${isUser
            ? 'bg-violet-600 text-white shadow-sm shadow-violet-900/20'
            : 'bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-sm shadow-violet-900/20'
          }`}
        aria-hidden
      >
        {isUser ? 'You' : 'AI'}
      </div>

      <div className={`flex flex-col max-w-[82%] sm:max-w-[75%]
        ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed transition-all
            ${isUser
              ? 'bg-violet-600 text-white rounded-tr-lg'
              : 'bg-[var(--color-surface-raised)] border border-[var(--color-border-subtle)] text-[var(--color-text-primary)] rounded-tl-lg'
            }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <>
              {displayContent ? (
                <div className="prose-chat">
                  <ReactMarkdown>{displayContent}</ReactMarkdown>
                </div>
              ) : isStreaming ? (
                <span className="inline-flex gap-1" aria-label="AI is typing">
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400 typing-dot" />
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400 typing-dot" />
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400 typing-dot" />
                </span>
              ) : null}
              {hasSources && <SourcePanel sources={sources!} />}
            </>
          )}
        </div>

        {createdAt && (
          <time
            dateTime={createdAt}
            className={`text-[10px] text-[var(--color-text-muted)] mt-1 px-1
              ${isUser ? 'text-right' : 'text-left'}`}
          >
            {formatMessageTime(createdAt)}
          </time>
        )}

        {!isUser && displayContent && !isStreaming && (
          <div
            className="mt-1 flex items-center gap-0.5 opacity-0 group-hover:opacity-100
              group-focus-within:opacity-100 transition-opacity duration-200"
            role="toolbar"
            aria-label="Message actions"
          >
            <ActionButton
              onClick={handleCopy}
              label={copied ? 'Copied' : 'Copy'}
              active={copied}
            >
              {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
            </ActionButton>

            {isLastAssistant && onRegenerate && (
              <ActionButton onClick={onRegenerate} label="Regenerate">
                <RotateCcw className="w-3.5 h-3.5" />
              </ActionButton>
            )}

            <ActionButton
              onClick={() => setFeedback(f => f === 'up' ? null : 'up')}
              label="Good response"
              active={feedback === 'up'}
            >
              <ThumbsUp className={`w-3.5 h-3.5 ${feedback === 'up' ? 'text-violet-400' : ''}`} />
            </ActionButton>

            <ActionButton
              onClick={() => setFeedback(f => f === 'down' ? null : 'down')}
              label="Bad response"
              active={feedback === 'down'}
            >
              <ThumbsDown className={`w-3.5 h-3.5 ${feedback === 'down' ? 'text-red-400' : ''}`} />
            </ActionButton>
          </div>
        )}
      </div>
    </article>
  )
}

function ActionButton({
  children,
  onClick,
  label,
  active,
}: {
  children: React.ReactNode
  onClick: () => void
  label: string
  active?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className={`p-1.5 rounded-lg text-[var(--color-text-muted)]
        hover:text-[var(--color-text-secondary)]
        hover:bg-[var(--color-surface-overlay)] transition-all
        ${active ? 'opacity-100' : ''}`}
    >
      {children}
    </button>
  )
}
