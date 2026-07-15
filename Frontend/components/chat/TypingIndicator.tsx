'use client'

interface Props {
  message?: string
}

export default function TypingIndicator({ message }: Props) {
  if (message) {
    return (
      <div className="flex items-start gap-3 animate-fade-in">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600
          to-indigo-600 flex items-center justify-center text-[10px]
          font-bold text-white shrink-0">
          AI
        </div>
        <div className="px-4 py-3 rounded-2xl rounded-tl-md
          bg-[var(--color-surface-raised)] border border-[var(--color-border-subtle)]
          text-sm text-[var(--color-text-secondary)]">
          {message}
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600
        to-indigo-600 flex items-center justify-center text-[10px]
        font-bold text-white shrink-0">
        AI
      </div>
      <div className="px-4 py-3.5 rounded-2xl rounded-tl-md
        bg-[var(--color-surface-raised)] border border-[var(--color-border-subtle)]
        flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-violet-400 typing-dot" />
        <span className="w-2 h-2 rounded-full bg-violet-400 typing-dot" />
        <span className="w-2 h-2 rounded-full bg-violet-400 typing-dot" />
      </div>
    </div>
  )
}
