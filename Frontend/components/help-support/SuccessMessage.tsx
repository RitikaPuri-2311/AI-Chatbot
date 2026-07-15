'use client'

import Link from 'next/link'
import { CheckCircle2, ExternalLink } from 'lucide-react'

interface Props {
  referenceKey: string
  ticketUrl?: string
  onCreateAnother: () => void
}

export default function SuccessMessage({
  referenceKey,
  ticketUrl,
  onCreateAnother,
}: Props) {
  return (
    <div
      role="status"
      className="rounded-2xl border border-green-500/25 bg-green-500/10
        p-6 sm:p-8 text-center space-y-5 animate-fade-in"
    >
      <div className="w-14 h-14 rounded-2xl bg-green-500/15 border border-green-500/25
        flex items-center justify-center mx-auto">
        <CheckCircle2 className="w-8 h-8 text-green-500" aria-hidden />
      </div>

      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Ticket submitted successfully
        </h2>
        <p className="text-sm text-[var(--color-text-muted)] mt-2">
          Our support team will review your request shortly.
        </p>
      </div>

      <div className="inline-flex flex-col items-center gap-1 px-5 py-3 rounded-2xl
        bg-[var(--color-surface-raised)] border border-[var(--color-border-subtle)]">
        <span className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">
          Jira Ticket Key
        </span>
        <span className="font-mono text-lg font-bold text-violet-500">
          {referenceKey}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
        {ticketUrl && (
          <a
            href={ticketUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5
              text-sm font-medium rounded-2xl bg-violet-600 text-white
              hover:bg-violet-500 transition-all shadow-sm shadow-violet-900/20"
          >
            <ExternalLink className="w-4 h-4" />
            View Ticket
          </a>
        )}
        <button
          type="button"
          onClick={onCreateAnother}
          className="px-5 py-2.5 text-sm font-medium rounded-2xl
            bg-[var(--color-surface-raised)] border border-[var(--color-border-subtle)]
            text-[var(--color-text-primary)] hover:border-violet-500/30
            transition-all"
        >
          Create Another Ticket
        </button>
        <Link
          href="/chat"
          className="px-5 py-2.5 text-sm font-medium rounded-2xl
            border border-[var(--color-border-subtle)]
            text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-overlay)]
            transition-all text-center"
        >
          Back to Chat
        </Link>
      </div>
    </div>
  )
}
