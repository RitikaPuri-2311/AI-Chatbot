'use client'

import type { ConversationOverview } from '@/types'

interface Props {
  data: ConversationOverview
}

const METRICS: {
  key: keyof ConversationOverview
  label: string
  format?: (value: string | number) => string
}[] = [
  {
    key: 'total_conversations',
    label: 'Total Conversations',
  },
  {
    key: 'average_messages',
    label: 'Avg Messages',
    format: (v) => String(v),
  },
  {
    key: 'average_duration',
    label: 'Avg Duration',
    format: (v) => String(v),
  },
  {
    key: 'most_used_persona',
    label: 'Top Persona',
    format: (v) => String(v).replace(/_/g, ' '),
  },
]

export default function SummaryCards({ data }: Props) {
  return (
    <section>
      <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
        Conversation Summary
      </h2>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {METRICS.map(({ key, label, format }) => {
          const raw = data[key]
          const display =
            format && raw != null ? format(raw) : String(raw ?? '—')

          return (
            <div
              key={key}
              className="rounded-xl border border-gray-200 dark:border-gray-700
                bg-gray-50 dark:bg-gray-800/50 p-4"
            >
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                {label}
              </p>
              <p className="text-xl font-semibold text-gray-800
                dark:text-gray-100 capitalize">
                {display}
              </p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
