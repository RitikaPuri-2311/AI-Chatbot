'use client'

import type { LucideIcon } from 'lucide-react'

interface Props {
  icon: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
}

export default function EmptyState({ icon: Icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 py-12
      text-center animate-fade-in" role="status">
      <div className="w-14 h-14 rounded-2xl bg-violet-600/10 border
        border-violet-500/15 flex items-center justify-center mb-4">
        <Icon className="w-7 h-7 text-violet-400" aria-hidden />
      </div>
      <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-xs text-[var(--color-text-muted)] max-w-xs leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
