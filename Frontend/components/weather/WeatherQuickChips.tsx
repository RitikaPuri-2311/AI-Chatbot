'use client'

import { Cloud } from 'lucide-react'
import { WEATHER_QUICK_ACTIONS } from '@/components/weather/weatherConfig'

interface Props {
  onSelect: (question: string) => void
  disabled?: boolean
}

export default function WeatherQuickChips({ onSelect, disabled }: Props) {
  return (
    <div className="shrink-0 flex flex-wrap gap-2 px-4 py-3 border-b
      border-[var(--color-border-subtle)]">
      <span className="flex items-center gap-1 text-[10px] font-semibold
        uppercase tracking-wider text-[var(--color-text-muted)] w-full mb-0.5">
        <Cloud className="w-3 h-3" />
        Quick actions
      </span>
      {WEATHER_QUICK_ACTIONS.map(({ label, question }) => (
        <button
          key={label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(question)}
          className="px-3 py-1.5 text-xs font-medium rounded-full
            border border-sky-500/20 bg-sky-600/10
            text-sky-300 hover:bg-sky-600/20 hover:border-sky-500/30
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-200"
        >
          {label}
        </button>
      ))}
    </div>
  )
}
