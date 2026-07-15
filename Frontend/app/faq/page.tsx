'use client'

import { useState } from 'react'
import { HelpCircle } from 'lucide-react'
import AppShell from '@/components/layout/AppShell'
import PageHeader from '@/components/layout/PageHeader'
import ChatWindow from '@/components/chat/ChatWindow'
import MessageInput from '@/components/chat/MessageInput'
import FaqQuickChips from '@/components/faq/FaqQuickChips'
import { FAQ_LOADING_MESSAGE } from '@/components/faq/faqConfig'
import { queryDocuments } from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import type { Message, Source } from '@/types'

export default function FaqPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId] = useState(() => `faq-${Date.now()}`)

  async function handleSend(content: string) {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    const aiMessageId = (Date.now() + 1).toString()

    try {
      const result = await queryDocuments(content, null, sessionId, { faqMode: true })

      setMessages(prev => [...prev, {
        id: aiMessageId,
        role: 'assistant',
        content: result.answer,
        sources: result.sources as Source[],
        createdAt: new Date().toISOString(),
      }])
    } catch {
      toast.error('Something went wrong. Please try again.')
      setMessages(prev => [...prev, {
        id: aiMessageId,
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
        createdAt: new Date().toISOString(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AppShell
      header={
        <PageHeader
          title="Company FAQ"
          subtitle="Ask questions about company policies and procedures"
          icon={<HelpCircle className="w-4 h-4 text-violet-500" />}
          user={user}
        />
      }
    >
      <FaqQuickChips onSelect={handleSend} disabled={isLoading} />

      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        isFaqMode
        onFaqQuestion={handleSend}
        loadingMessage={FAQ_LOADING_MESSAGE}
      />

      <MessageInput
        onSend={handleSend}
        isLoading={isLoading}
        showAttach={false}
        placeholder="Ask about returns, warranty, shipping, cancellation..."
      />
    </AppShell>
  )
}
