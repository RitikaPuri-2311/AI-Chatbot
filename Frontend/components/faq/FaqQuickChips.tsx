'use client'

import { FAQ_QUICK_ACTIONS } from '@/components/faq/faqConfig'

interface Props {
  onSelect: (question: string) => void
  disabled?: boolean
}

export default function FaqQuickChips({ onSelect, disabled }: Props) {
  return (
    <div className="flex flex-wrap gap-2 px-6 pb-3">
      {FAQ_QUICK_ACTIONS.map(({ label, question }) => (
        <button
          key={label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(question)}
          className="px-3 py-1.5 text-xs font-medium rounded-full
            border border-indigo-200 dark:border-indigo-800
            bg-indigo-50 dark:bg-indigo-950/40
            text-indigo-700 dark:text-indigo-300
            hover:bg-indigo-100 dark:hover:bg-indigo-900/50
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors"
        >
          {label}
        </button>
      ))}
    </div>
  )
}
