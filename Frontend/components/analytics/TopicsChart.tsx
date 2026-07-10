'use client'

import type { TopicCount } from '@/types'

interface Props {
  topics: TopicCount[]
}

export default function TopicsChart({ topics }: Props) {
  const maxCount = Math.max(...topics.map((t) => t.count), 1)

  if (topics.length === 0) {
    return (
      <section className="rounded-xl border border-gray-200
        dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6">
        <h2 className="text-sm font-semibold text-gray-700
          dark:text-gray-200 mb-3">
          Topics
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No topic data yet. Topics appear after support conversations
          are recorded.
        </p>
      </section>
    )
  }

  return (
    <section className="rounded-xl border border-gray-200
      dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6">
      <h2 className="text-sm font-semibold text-gray-700
        dark:text-gray-200 mb-4">
        Topics
      </h2>
      <ul className="space-y-3">
        {topics.map(({ topic, count }) => (
          <li key={topic}>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-700 dark:text-gray-300 font-medium">
                {topic}
              </span>
              <span className="text-gray-500 dark:text-gray-400 tabular-nums">
                {count}
              </span>
            </div>
            <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700
              overflow-hidden">
              <div
                className="h-full rounded-full bg-indigo-600
                  dark:bg-indigo-500 transition-all"
                style={{ width: `${(count / maxCount) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
