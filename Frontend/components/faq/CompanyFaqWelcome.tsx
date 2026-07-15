'use client'

import { HelpCircle } from 'lucide-react'
import { FAQ_POPULAR_QUESTIONS } from '@/components/faq/faqConfig'

interface Props {
  onQuestionClick: (question: string) => void
  disabled?: boolean
}

export default function CompanyFaqWelcome({
  onQuestionClick,
  disabled,
}: Props) {
  return (
    <div className="flex items-center justify-center flex-1 px-4 py-8 animate-fade-in">
      <div className="max-w-lg w-full rounded-2xl border border-[var(--color-border-subtle)]
        bg-[var(--color-surface-raised)] p-8 shadow-sm">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-violet-600/15 border
            border-violet-500/20 flex items-center justify-center mx-auto mb-4">
            <HelpCircle className="w-7 h-7 text-violet-400" />
          </div>
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Company Knowledge Base
          </h2>
          <p className="text-sm text-[var(--color-text-muted)] mt-2 leading-relaxed">
            Ask questions about company policies and get answers directly
            from the uploaded FAQ document.
          </p>
        </div>

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider
            text-[var(--color-text-muted)] mb-3">
            Popular Questions
          </p>
          <ul className="space-y-1">
            {FAQ_POPULAR_QUESTIONS.map(question => (
              <li key={question}>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => onQuestionClick(question)}
                  className="w-full text-left text-sm px-3 py-2.5 rounded-xl
                    text-[var(--color-text-secondary)] hover:text-violet-300
                    hover:bg-violet-600/10 disabled:opacity-50
                    disabled:cursor-not-allowed transition-all duration-150"
                >
                  {question}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
