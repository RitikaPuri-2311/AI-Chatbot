'use client'

import { useState } from 'react'
import { ChevronDown, FileText } from 'lucide-react'
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
    <div className="mt-3 pt-3 border-t border-[var(--color-border-subtle)]">
      <p className="text-[10px] font-semibold uppercase tracking-wider
        text-[var(--color-text-muted)] mb-2 flex items-center gap-1.5">
        <FileText className="w-3 h-3" />
        Sources
      </p>

      <ul className="space-y-0.5 mb-3">
        {grouped.map(({ name, pages }) => (
          <li
            key={name}
            className="text-xs text-[var(--color-text-secondary)]"
          >
            • {name} — {formatPageLabel(pages)}
          </li>
        ))}
      </ul>

      <div className="flex flex-col gap-1.5">
        {sources.map((source, i) => (
          <div
            key={`${source.source}-${source.page}-${i}`}
            className="border border-[var(--color-border-subtle)] rounded-xl
              overflow-hidden bg-[var(--color-surface)]"
          >
            <button
              type="button"
              className="flex items-center justify-between w-full px-3 py-2
                cursor-pointer hover:bg-[var(--color-surface-overlay)]
                transition-colors text-left"
              onClick={() => setExpanded(expanded === i ? null : i)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-xs font-medium text-violet-400 shrink-0">
                  Page {source.page}
                </span>
                <span className="text-xs text-[var(--color-text-muted)] truncate">
                  {source.source}
                </span>
                {source.similarity != null && (
                  <span className="text-[10px] text-[var(--color-text-muted)] shrink-0">
                    {Math.round(source.similarity * 100)}%
                  </span>
                )}
              </div>
              <ChevronDown
                className={`w-3.5 h-3.5 text-[var(--color-text-muted)] shrink-0
                  transition-transform duration-200
                  ${expanded === i ? 'rotate-180' : ''}`}
              />
            </button>

            {expanded === i && (
              <div className="px-3 py-2 border-t border-[var(--color-border-subtle)]">
                <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
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
