'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { sendMessage, getMessages } from '@/lib/api'
import { logout } from '@/lib/auth'
import ChatWindow from '@/components/chat/ChatWindow'
import MessageInput from '@/components/chat/MessageInput'
import type { Message } from '@/types'

export default function ChatPage() {
  const { user, loading } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    async function loadMessages() {
      try {
        const data = await getMessages()
        setMessages(data)
      } catch {
        console.error('Failed to load messages')
      }
    }
    loadMessages()
  }, [])

  async function handleSend(content: string) {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const aiReply = await sendMessage(content)
      setMessages(prev => [...prev, aiReply])
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
        createdAt: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400 text-sm">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 
      px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-800">
            AI Chatbot
          </h1>
          {user && (
            <p className="text-xs text-gray-400">
              Logged in as {user.username}
            </p>
          )}
        </div>
        <button
          onClick={logout}
          className="text-sm text-gray-500 hover:text-red-500 
          transition-colors"
        >
          Logout
        </button>
      </header>

      <div className="flex-1 flex flex-col max-w-3xl w-full 
      mx-auto bg-white shadow-sm min-h-0">
        <ChatWindow messages={messages} isLoading={isLoading} />
        <MessageInput onSend={handleSend} isLoading={isLoading} />
      </div>
    </div>
  )
}