'use client'

import { useEffect, useRef } from 'react'
import type { Message } from '@/types'
import MessageBubble from '@/components/chat/MessageBubble'
import TypingIndicator from '@/components/chat/TypingIndicator'
import SuggestedPrompts from '@/components/chat/SuggestedPrompts'
import CompanyFaqWelcome from '@/components/faq/CompanyFaqWelcome'
import { ChatSkeleton } from '@/components/ui/Skeleton'

interface Prompt {
  title: string
  prompt: string
}

interface Props {
  messages: Message[]
  isLoading: boolean
  isLoadingMessages?: boolean
  isFaqMode?: boolean
  onFaqQuestion?: (question: string) => void
  loadingMessage?: string
  suggestedPrompts?: readonly Prompt[]
  onSuggestedPrompt?: (prompt: string) => void
  streamingMessageId?: string | null
  onRegenerate?: () => void
}

export default function ChatWindow({
  messages,
  isLoading,
  isLoadingMessages,
  isFaqMode = false,
  onFaqQuestion,
  loadingMessage,
  suggestedPrompts,
  onSuggestedPrompt,
  streamingMessageId,
  onRegenerate,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const hasUserMessages = messages.some(m => m.role === 'user')
  const showFaqWelcome = isFaqMode && !hasUserMessages && !isLoading && !isLoadingMessages
  const showSuggested =
    !isFaqMode &&
    !hasUserMessages &&
    !isLoading &&
    !isLoadingMessages &&
    suggestedPrompts &&
    onSuggestedPrompt

  const lastAssistantIdx = [...messages].reverse().findIndex(m => m.role === 'assistant')
  const lastAssistantId = lastAssistantIdx >= 0
    ? messages[messages.length - 1 - lastAssistantIdx]?.id
    : null

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (isLoadingMessages) {
    return (
      <div className="flex-1 overflow-y-auto" aria-busy="true">
        <ChatSkeleton />
      </div>
    )
  }

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-6 flex flex-col gap-5 min-h-full">
        {showFaqWelcome && onFaqQuestion ? (
          <CompanyFaqWelcome onQuestionClick={onFaqQuestion} disabled={isLoading} />
        ) : showSuggested ? (
          <SuggestedPrompts
            prompts={suggestedPrompts}
            onSelect={onSuggestedPrompt}
            disabled={isLoading}
          />
        ) : null}

        {messages.map(message => (
          <MessageBubble
            key={message.id}
            role={message.role}
            content={message.content}
            createdAt={message.createdAt}
            sources={message.sources}
            isStreaming={
              isLoading &&
              message.id === streamingMessageId &&
              message.role === 'assistant' &&
              !message.content
            }
            isLastAssistant={
              message.role === 'assistant' && message.id === lastAssistantId
            }
            onRegenerate={
              message.role === 'assistant' && message.id === lastAssistantId
                ? onRegenerate
                : undefined
            }
          />
        ))}

        {isLoading && !streamingMessageId && (
          <TypingIndicator message={loadingMessage} />
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
