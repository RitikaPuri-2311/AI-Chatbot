'use client'

import { useEffect, useRef } from 'react'
import type { Message } from '@/types'
import MessageBubble from '@/components/chat/MessageBubble'
import CompanyFaqWelcome from '@/components/faq/CompanyFaqWelcome'

interface Props {
  messages: Message[]
  isLoading: boolean
  isFaqMode?: boolean
  onFaqQuestion?: (question: string) => void
  loadingMessage?: string
}

export default function ChatWindow({
  messages,
  isLoading,
  isFaqMode = false,
  onFaqQuestion,
  loadingMessage,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const hasUserMessages = messages.some(m => m.role === 'user')
  const showFaqWelcome = isFaqMode && !hasUserMessages && !isLoading

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4 bg-white dark:bg-gray-900">
      {showFaqWelcome && onFaqQuestion ? (
        <CompanyFaqWelcome
          onQuestionClick={onFaqQuestion}
          disabled={isLoading}
        />
      ) : messages.length === 0 && !isLoading && !isFaqMode ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-400 text-sm">
            Send a message to start the conversation
          </p>
        </div>
      ) : null}

      {messages.map(message => (
        <MessageBubble
          key={message.id}
          role={message.role}
          content={message.content}
          sources={message.sources}
        />
      ))}

      {isLoading && (
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full flex items-center
            justify-center text-xs font-semibold shrink-0 mt-1
            bg-gray-800 dark:bg-gray-600 text-white">
            AI
          </div>
          <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl
            rounded-tl-sm px-4 py-3 text-sm text-gray-600
            dark:text-gray-300">
            {loadingMessage ?? (
              <div className="flex gap-1 items-center">
                <span className="w-2 h-2 bg-gray-400 rounded-full
                  animate-bounce [animation-delay:0ms]"/>
                <span className="w-2 h-2 bg-gray-400 rounded-full
                  animate-bounce [animation-delay:150ms]"/>
                <span className="w-2 h-2 bg-gray-400 rounded-full
                  animate-bounce [animation-delay:300ms]"/>
              </div>
            )}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
