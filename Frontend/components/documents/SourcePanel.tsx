'use client'

import { useState } from 'react'
import type { Source } from '@/types'
import {
  groupSourcesByDocument,
  formatPageLabel,
} from '@/lib/citations'

interface Props {
  sources: Source[]
}

export default function SourcePanel({ sources }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null)

  if (!sources || sources.length === 0) return null

  const grouped = groupSourcesByDocument(sources)

  return (
    <div className="mt-3 pt-3 border-t border-gray-200
      dark:border-gray-700">
      <p className="text-xs font-medium text-gray-600
        dark:text-gray-300 mb-2">
        📄 Sources
      </p>

      <ul className="space-y-1 mb-3">
        {grouped.map(({ name, pages }) => (
          <li
            key={name}
            className="text-xs text-gray-600 dark:text-gray-300"
          >
            • {name} — {formatPageLabel(pages)}
          </li>
        ))}
      </ul>

      <div className="flex flex-col gap-2">
        {sources.map((source, i) => (
          <div
            key={`${source.source}-${source.page}-${i}`}
            className="border border-gray-200 dark:border-gray-700
              rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-800/50"
          >
            <div
              className="flex items-center justify-between px-3 py-2
                cursor-pointer hover:bg-gray-100
                dark:hover:bg-gray-700/50 transition-colors"
              onClick={() => setExpanded(expanded === i ? null : i)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-xs font-medium text-indigo-600
                  dark:text-indigo-400 shrink-0">
                  Page {source.page}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400
                  truncate">
                  {source.source}
                </span>
                {source.similarity != null && (
                  <span className="text-xs text-gray-400
                    dark:text-gray-500 shrink-0">
                    {Math.round(source.similarity * 100)}% match
                  </span>
                )}
              </div>

              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className={`w-3.5 h-3.5 text-gray-400 shrink-0
                  transition-transform
                  ${expanded === i ? 'rotate-180' : ''}`}
              >
                <path
                  fillRule="evenodd"
                  d="M12.53 16.28a.75.75 0 01-1.06 0l-7.5-7.5a.75.75
                  0 011.06-1.06L12 14.69l6.97-6.97a.75.75 0 111.06
                  1.06l-7.5 7.5z"
                  clipRule="evenodd"
                />
              </svg>
            </div>

            {expanded === i && (
              <div className="px-3 py-2 border-t border-gray-200
                dark:border-gray-700">
                <p className="text-xs text-gray-600 dark:text-gray-300
                  leading-relaxed">
                  {source.text_snippet}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
