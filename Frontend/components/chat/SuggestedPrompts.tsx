'use client'

import { Sparkles } from 'lucide-react'

interface Prompt {
  title: string
  prompt: string
}

interface Props {
  prompts: readonly Prompt[]
  onSelect: (prompt: string) => void
  disabled?: boolean
}

export default function SuggestedPrompts({ prompts, onSelect, disabled }: Props) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4 py-10
      animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600/20
        to-indigo-600/20 border border-violet-500/20 flex items-center
        justify-center mb-6 shadow-lg shadow-violet-900/10
        hover:scale-105 transition-transform duration-300">
        <Sparkles className="w-8 h-8 text-violet-400" aria-hidden />
      </div>
      <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
        How can I help you today?
      </h2>
      <p className="text-sm text-[var(--color-text-muted)] mb-8 text-center max-w-md">
        Ask anything — explanations, code, brainstorming, summaries, and more.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
        {prompts.map(item => (
          <button
            key={item.title}
            type="button"
            onClick={() => onSelect(item.prompt)}
            disabled={disabled}
            className="text-left px-4 py-4 rounded-2xl border
              border-[var(--color-border-subtle)] bg-[var(--color-surface-raised)]
              hover:border-violet-500/35 hover:bg-violet-600/5
              hover:-translate-y-0.5 hover:shadow-md hover:shadow-violet-900/10
              transition-all duration-200 disabled:opacity-50
              disabled:cursor-not-allowed disabled:hover:translate-y-0
              focus-visible:ring-2 focus-visible:ring-violet-500/40"
          >
            <p className="text-sm font-medium text-[var(--color-text-primary)]
              group-hover:text-violet-300">
              {item.title}
            </p>
            <p className="text-xs text-[var(--color-text-muted)] mt-1 line-clamp-2">
              {item.prompt}
            </p>
          </button>
        ))}
      </div>
    </div>
  )
}
