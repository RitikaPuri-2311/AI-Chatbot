'use client'
import type { Role, Source } from '@/types'
import ReactMarkdown from 'react-markdown'
import SourcePanel from '@/components/documents/SourcePanel'
import { stripEmbeddedCitations } from '@/lib/citations'

interface Props {
  role: Role
  content: string
  sources?: Source[]
}

export default function MessageBubble({ role, content, sources }: Props) {
  const isUser = role === 'user'
  const hasSources = Boolean(sources && sources.length > 0)
  const displayContent = hasSources
    ? stripEmbeddedCitations(content)
    : content

  return (
    <div className={`flex gap-3 items-start
      ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>

      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center
        justify-center text-xs font-semibold shrink-0 mt-1
        ${isUser
          ? 'bg-indigo-600 text-white'
          : 'bg-gray-800 dark:bg-gray-600 text-white'
        }`}>
        {isUser ? 'You' : 'AI'}
      </div>

      {/* Message + Sources */}
      <div className={`max-w-[75%] px-4 py-3 rounded-2xl
        text-sm leading-relaxed
        ${isUser
          ? 'bg-indigo-600 text-white rounded-tr-sm'
          : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-tl-sm'
        }`}>
        {isUser ? (
          content
        ) : (
          <>
            <ReactMarkdown
              components={{
                p: ({ children }) => (
                  <p className="mb-2 last:mb-0">{children}</p>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-2 space-y-1">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside mb-2 space-y-1">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-sm">{children}</li>
                ),
                code: ({ children }) => (
                  <code className="bg-gray-200 dark:bg-gray-700
                    text-gray-800 dark:text-gray-100
                    px-1 py-0.5 rounded text-xs font-mono">
                    {children}
                  </code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-gray-200 dark:bg-gray-700
                    text-gray-800 dark:text-gray-100
                    p-3 rounded-lg text-xs font-mono
                    overflow-x-auto mt-2 mb-2">
                    {children}
                  </pre>
                ),
              }}
            >
              {displayContent}
            </ReactMarkdown>

            {hasSources && (
              <SourcePanel sources={sources!} />
            )}
          </>
        )}
      </div>
    </div>
  )
}