'use client'

import type { SentimentAnalytics } from '@/types'

interface Props {
  data: SentimentAnalytics
}

const SENTIMENT_CONFIG = [
  {
    key: 'positive' as const,
    label: 'Positive',
    barClass: 'bg-emerald-500',
    textClass: 'text-emerald-600 dark:text-emerald-400',
  },
  {
    key: 'neutral' as const,
    label: 'Neutral',
    barClass: 'bg-gray-400 dark:bg-gray-500',
    textClass: 'text-gray-600 dark:text-gray-400',
  },
  {
    key: 'negative' as const,
    label: 'Negative',
    barClass: 'bg-rose-500',
    textClass: 'text-rose-600 dark:text-rose-400',
  },
]

function toPercent(value: number, total: number): number {
  if (total <= 0) return 0
  return Math.round((value / total) * 100)
}

export default function SentimentPanel({ data }: Props) {
  const total = data.positive + data.neutral + data.negative

  return (
    <section className="rounded-xl border border-gray-200
      dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6">
      <h2 className="text-sm font-semibold text-gray-700
        dark:text-gray-200 mb-4">
        Sentiment
      </h2>

      {total === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No sentiment data yet.
        </p>
      ) : (
        <div className="space-y-4">
          {SENTIMENT_CONFIG.map(({ key, label, barClass, textClass }) => {
            const count = data[key]
            const pct = toPercent(count, total)

            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-sm font-medium ${textClass}`}>
                    {label}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400
                    tabular-nums">
                    {pct}% ({count})
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-gray-200
                  dark:bg-gray-700 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${barClass}
                      transition-all`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}

          <div className="flex gap-2 pt-2">
            {SENTIMENT_CONFIG.map(({ key, label, barClass }) => {
              const pct = toPercent(data[key], total)
              if (pct === 0) return null
              return (
                <div
                  key={key}
                  className="flex-1 rounded-lg border border-gray-200
                    dark:border-gray-700 bg-white dark:bg-gray-900 p-3
                    text-center"
                >
                  <div
                    className={`w-3 h-3 rounded-full mx-auto mb-2
                      ${barClass}`}
                  />
                  <p className="text-lg font-semibold text-gray-800
                    dark:text-gray-100 tabular-nums">
                    {pct}%
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {label}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </section>
  )
}
