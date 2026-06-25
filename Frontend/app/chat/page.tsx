'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/components/ThemeProvider'
import { sendMessage, getMessages } from '@/lib/api'
import { logout } from '@/lib/auth'
import ChatWindow from '@/components/chat/ChatWindow'
import MessageInput from '@/components/chat/MessageInput'
import type { Message } from '@/types'

export default function ChatPage() {
  const { user, loading } = useAuth()
  const { theme, toggleTheme } = useTheme()
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
        justify-center bg-gray-50 dark:bg-gray-950">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-600 
            border-t-transparent rounded-full animate-spin"/>
          <p className="text-sm text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 
      overflow-hidden">

      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 dark:bg-gray-950 
        flex flex-col shrink-0">

        {/* Logo */}
        <div className="px-4 py-5 border-b border-gray-700 
          dark:border-gray-800">
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
        <div className="px-3 py-4 border-t border-gray-700
          dark:border-gray-800">
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
          dark:border-gray-700 bg-white dark:bg-gray-900
          flex items-center justify-between">
          <div>
            <h1 className="text-sm font-medium text-gray-700 
              dark:text-gray-200">
              New Conversation
            </h1>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              Powered by AI
            </p>
          </div>

          {/* Dark mode toggle */}
          <button
            onClick={toggleTheme}
            className="text-gray-500 dark:text-gray-400 
            hover:text-gray-700 dark:hover:text-gray-200 
            transition-colors p-2 rounded-lg 
            hover:bg-gray-100 dark:hover:bg-gray-800"
            title="Toggle dark mode"
          >
            {theme === 'light' ? (
              <svg xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24" fill="currentColor"
                className="w-5 h-5">
                <path fillRule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24" fill="currentColor"
                className="w-5 h-5">
                <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
              </svg>
            )}
          </button>
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