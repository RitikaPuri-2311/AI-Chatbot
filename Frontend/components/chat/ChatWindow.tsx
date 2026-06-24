'use client'
import { useEffect, useRef } from 'react'
import type { Message } from '@/types'
import MessageBubble from '@/components/chat/MessageBubble'

interface Props {
  messages: Message[]
  isLoading: boolean
}

export default function ChatWindow({ messages, isLoading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4">
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-400 text-sm">
            Send a message to start the conversation
          </p>
        </div>
      )}

      {messages.map(message => (
        <MessageBubble
          key={message.id}
          role={message.role}
          content={message.content}
        />
      ))}

      {isLoading && (
        <div className="flex items-start gap-1">
          <span className="text-xs text-gray-400 px-1 mb-1">AI</span>
          <div className="bg-gray-100 rounded-2xl rounded-tl-sm 
          px-4 py-3">
            <div className="flex gap-1 items-center">
              <span className="w-2 h-2 bg-gray-400 rounded-full 
              animate-bounce [animation-delay:0ms]"/>
              <span className="w-2 h-2 bg-gray-400 rounded-full 
              animate-bounce [animation-delay:150ms]"/>
              <span className="w-2 h-2 bg-gray-400 rounded-full 
              animate-bounce [animation-delay:300ms]"/>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}