'use client'

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
    <div className="flex items-center justify-center h-full px-4 py-8">
      <div className="max-w-lg w-full rounded-2xl border border-gray-200
        dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-6 shadow-sm">
        <div className="text-center mb-6">
          <div className="text-3xl mb-3">📋</div>
          <h2 className="text-base font-semibold text-gray-800
            dark:text-gray-100">
            Company Knowledge Base
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2
            leading-relaxed">
            Ask questions about company policies and get answers directly
            from the uploaded FAQ document.
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide
            text-gray-500 dark:text-gray-400 mb-3">
            Popular Questions
          </p>
          <ul className="space-y-2">
            {FAQ_POPULAR_QUESTIONS.map(question => (
              <li key={question}>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => onQuestionClick(question)}
                  className="w-full text-left text-sm text-indigo-600
                    dark:text-indigo-400 hover:text-indigo-800
                    dark:hover:text-indigo-300 disabled:opacity-50
                    disabled:cursor-not-allowed transition-colors
                    flex items-start gap-2"
                >
                  <span className="text-gray-400 shrink-0">•</span>
                  <span>{question}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
