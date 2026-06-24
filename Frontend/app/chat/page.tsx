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
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
        createdAt: new Date().toISOString(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center 
        justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-600 
            border-t-transparent rounded-full animate-spin"/>
          <p className="text-sm text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 flex flex-col 
        shrink-0">
        
        {/* Logo */}
        <div className="px-4 py-5 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-indigo-600 rounded-lg 
              flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" fill="currentColor" 
                className="w-4 h-4 text-white">
                <path d="M4.913 2.658c2.075-.27 4.19-.408 
                6.337-.408 2.147 0 4.262.139 6.337.408 
                1.922.25 3.291 1.861 3.405 3.727a4.403 
                4.403 0 00-1.032-.211 50.89 50.89 0 
                00-8.42 0c-2.358.196-4.04 2.19-4.04 
                4.434v4.286a4.47 4.47 0 002.433 
                3.984L7.28 21.53A.75.75 0 016 
                21v-4.03a48.527 48.527 0 
                01-1.087-.128C2.905 16.58 1.5 14.833 
                1.5 12.862V6.638c0-1.97 1.405-3.718 
                3.413-3.979z" />
                <path d="M15.75 7.5c-1.376 0-2.739.057-4.086.169C10.124 
                7.797 9 9.103 9 10.609v4.285c0 1.507 1.128 
                2.814 2.664 2.94 1.243.102 2.5.157 3.768.157 
                .767 0 1.526-.032 2.276-.094l3.772 3.682a.75.75 
                0 001.28-.53v-3.645a3.375 3.375 0 
                001.436-2.81v-4.24c0-1.507-1.128-2.814-2.664-2.94A49.138 
                49.138 0 0015.75 7.5z" />
              </svg>
            </div>
            <span className="text-white font-semibold text-sm">
              AI Chatbot
            </span>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="px-3 pt-4">
          <button
            onClick={() => setMessages([])}
            className="w-full flex items-center gap-2 px-3 py-2 
            text-sm text-gray-300 hover:bg-gray-700 rounded-lg 
            transition-colors border border-gray-600 
            hover:border-gray-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" fill="currentColor" 
              className="w-4 h-4">
              <path fillRule="evenodd" d="M12 3.75a.75.75 
              0 01.75.75v6.75h6.75a.75.75 0 010 
              1.5h-6.75v6.75a.75.75 0 01-1.5 
              0v-6.75H4.5a.75.75 0 010-1.5h6.75V4.5a.75.75 
              0 01.75-.75z" clipRule="evenodd" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* User + Logout */}
        <div className="px-3 py-4 border-t border-gray-700">
          <div className="flex items-center gap-3 px-2 py-2 
            rounded-lg hover:bg-gray-700 transition-colors">
            <div className="w-7 h-7 bg-indigo-600 rounded-full 
              flex items-center justify-center text-xs 
              font-semibold text-white shrink-0">
              {user?.username?.charAt(0).toUpperCase() ?? 'U'}
            </div>
            <span className="text-sm text-gray-300 
              truncate flex-1">
              {user?.username ?? 'User'}
            </span>
            <button
              onClick={logout}
              title="Logout"
              className="text-gray-500 hover:text-red-400 
              transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" fill="currentColor" 
                className="w-4 h-4">
                <path fillRule="evenodd" d="M7.5 3.75A1.5 
                1.5 0 006 5.25v13.5a1.5 1.5 0 001.5 
                1.5h6a1.5 1.5 0 001.5-1.5V15a.75.75 
                0 011.5 0v3.75a3 3 0 01-3 3h-6a3 3 
                0 01-3-3V5.25a3 3 0 013-3h6a3 3 0 
                013 3V9A.75.75 0 0115 9V5.25a1.5 1.5 
                0 00-1.5-1.5h-6zm10.72 4.72a.75.75 0 
                011.06 0l3 3a.75.75 0 010 1.06l-3 
                3a.75.75 0 11-1.06-1.06l1.72-1.72H9a.75.75 
                0 010-1.5h10.94l-1.72-1.72a.75.75 0 
                010-1.06z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 
          bg-white">
          <h1 className="text-sm font-medium text-gray-700">
            New Conversation
          </h1>
          <p className="text-xs text-gray-400">
            Powered by AI
          </p>
        </div>

        {/* Chat */}
        <ChatWindow 
          messages={messages} 
          isLoading={isLoading} 
        />

        {/* Input */}
        <MessageInput 
          onSend={handleSend} 
          isLoading={isLoading} 
        />
      </main>
    </div>
  )
}