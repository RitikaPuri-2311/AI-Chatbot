'use client'

import type { QuickAction } from '@/components/help-support/helpSupportConfig'

interface Props {
  action: QuickAction
  selected: boolean
  onSelect: (action: QuickAction) => void
}

export default function IssueTypeCard({ action, selected, onSelect }: Props) {
  return (
    <button
      type="button"
      onClick={() => onSelect(action)}
      className={`flex flex-col items-start gap-2 p-4 rounded-2xl border
        text-left transition-all duration-200 w-full
        hover:-translate-y-0.5
        ${selected
          ? 'border-violet-500/40 bg-violet-600/10 ring-1 ring-violet-500/30'
          : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-raised)] hover:border-violet-500/30 hover:bg-violet-600/5'
        }`}
    >
      <span className="text-2xl" aria-hidden>{action.emoji}</span>
      <span className="text-sm font-medium text-[var(--color-text-primary)]">
        {action.label}
      </span>
    </button>
  )
}
