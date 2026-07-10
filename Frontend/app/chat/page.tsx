'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/components/ThemeProvider'
import {
  sendMessage,
  getMessages,
  getSessions,
  createSession,
  deleteSession,
  queryDocuments
} from '@/lib/api'
import { logout } from '@/lib/auth'
import ChatWindow from '@/components/chat/ChatWindow'
import MessageInput from '@/components/chat/MessageInput'
import FaqQuickChips from '@/components/faq/FaqQuickChips'
import { FAQ_LOADING_MESSAGE } from '@/components/faq/faqConfig'
import AnalyticsDashboard from '@/components/analytics/AnalyticsDashboard'
import DocumentPanel, { type DocumentScope } from '@/components/documents/DocumentPanel'
import toast from 'react-hot-toast'
import type { Message, ChatSession, Source } from '@/types'

export type SidebarMode = 'chat' | 'documents' | 'faq' | 'analytics'

export default function ChatPage() {
  const { user, loading } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string>('')
  const [persona, setPersona] = useState<string>('default')
  const [sidebarMode, setSidebarMode] = useState<SidebarMode>('chat')
  const [documentScope, setDocumentScope] = useState<DocumentScope>('chat')
  const [sidebarTab, setSidebarTab] = useState<'chat' | 'docs'>('chat')

  const isFaqMode = sidebarMode === 'faq'
  const isAnalyticsMode = sidebarMode === 'analytics'
  const isDocumentQueryMode =
    sidebarMode === 'documents' && documentScope !== 'chat'
  const selectedDocId =
    documentScope !== 'chat' && documentScope !== 'all'
      ? documentScope
      : null

  useEffect(() => {
    if (!user) return
    loadSessions()
  }, [user])

  useEffect(() => {
    if (!activeSessionId) return
    loadMessages(activeSessionId)
  }, [activeSessionId])

  async function loadSessions() {
    const data = await getSessions()
    setSessions(data)
    if (data.length > 0) {
      setActiveSessionId(data[0].id)
    } else {
      handleNewChat()
    }
  }

  async function loadMessages(sessionId: string) {
    const data = await getMessages(sessionId)
    setMessages(data)
  }

  async function handleNewChat() {
    const session = await createSession()
    if (!session) return
    setSessions(prev => [session, ...prev])
    setActiveSessionId(session.id)
    setMessages([])
    toast.success('New chat started!')
  }

  async function handleSelectSession(sessionId: string) {
    setActiveSessionId(sessionId)
    setMessages([])
  }

  async function handleDeleteSession(sessionId: string) {
    const success = await deleteSession(sessionId)
    if (!success) return
    const remaining = sessions.filter(s => s.id !== sessionId)
    setSessions(remaining)
    if (activeSessionId === sessionId) {
      if (remaining.length > 0) {
        setActiveSessionId(remaining[0].id)
      } else {
        handleNewChat()
      }
    }
  }

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
      if (isFaqMode) {
        const result = await queryDocuments(
          content,
          null,
          activeSessionId,
          { faqMode: true }
        )

        setMessages(prev => [...prev, {
          id: aiMessageId,
          role: 'assistant',
          content: result.answer,
          sources: result.sources as Source[],
          createdAt: new Date().toISOString(),
        }])
      } else {
        // Add empty AI message placeholder for streaming / doc search
        setMessages(prev => [...prev, {
          id: aiMessageId,
          role: 'assistant',
          content: '',
          createdAt: new Date().toISOString(),
        }])

        if (isDocumentQueryMode) {
          const docId = documentScope === 'all' ? null : documentScope

          setMessages(prev => prev.map(msg =>
            msg.id === aiMessageId
              ? {
                  ...msg,
                  content: documentScope === 'all'
                    ? '🔍 Searching all documents...'
                    : '🔍 Searching document...'
                }
              : msg
          ))

          const result = await queryDocuments(
            content,
            docId,
            activeSessionId
          )

          setMessages(prev => prev.map(msg =>
            msg.id === aiMessageId
              ? {
                  ...msg,
                  content: result.answer,
                  sources: result.sources as Source[]
                }
              : msg
          ))
        } else {
          await sendMessage(
            content,
            activeSessionId,
            persona,
            (chunk: string) => {
              setMessages(prev => prev.map(msg =>
                msg.id === aiMessageId
                  ? { ...msg, content: msg.content + chunk }
                  : msg
              ))
            }
          )
        }
      }

      const updatedSessions = await getSessions()
      setSessions(updatedSessions)

    } catch (err: unknown) {
      const message = err instanceof Error
        ? err.message : 'Something went wrong'

      if (!message.includes('quota') &&
          !message.includes('rate')) {
        toast.error('Something went wrong. Please try again.')
      }

      if (isFaqMode) {
        setMessages(prev => [...prev, {
          id: aiMessageId,
          role: 'assistant',
          content: 'Something went wrong. Please try again.',
          createdAt: new Date().toISOString(),
        }])
      } else {
        setMessages(prev => prev.map(msg =>
          msg.id === aiMessageId
            ? { ...msg, content: 'Something went wrong. Please try again.' }
            : msg
        ))
      }
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

  const activeSession = sessions.find(s => s.id === activeSessionId)

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

        {/* Sidebar tabs */}
        <div className="flex border-b border-gray-700
          dark:border-gray-800">
          <button
            onClick={() => {
              setSidebarTab('chat')
              setSidebarMode('chat')
            }}
            className={`flex-1 py-2 text-xs font-medium
              transition-colors
              ${sidebarTab === 'chat'
                ? 'text-white border-b-2 border-indigo-500'
                : 'text-gray-500 hover:text-gray-300'
              }`}
          >
            Chats
          </button>
          <button
            onClick={() => {
              setSidebarTab('docs')
              setSidebarMode('documents')
            }}
            className={`flex-1 py-2 text-xs font-medium
              transition-colors relative
              ${sidebarTab === 'docs'
                ? 'text-white border-b-2 border-indigo-500'
                : 'text-gray-500 hover:text-gray-300'
              }`}
          >
            Documents
            {isDocumentQueryMode && (
              <span className="absolute top-1.5 right-3 w-2 h-2
                bg-green-400 rounded-full"/>
            )}
          </button>
        </div>

        {/* Company FAQ — below Documents tab */}
        <button
          onClick={() => {
            setSidebarMode('faq')
            setSidebarTab('chat')
            setDocumentScope('chat')
          }}
          className={`w-full flex items-center gap-2 px-4 py-2.5 text-xs
            font-medium transition-colors border-b border-gray-700
            dark:border-gray-800 relative
            ${isFaqMode
              ? 'bg-indigo-900/40 text-indigo-200 border-l-2 border-l-indigo-500'
              : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
            }`}
        >
          <span>📋</span>
          <span>Company FAQ</span>
          {isFaqMode && (
            <span className="absolute right-4 w-2 h-2 bg-green-400 rounded-full"/>
          )}
        </button>

        {/* Analytics — below Company FAQ */}
        <button
          onClick={() => {
            setSidebarMode('analytics')
            setSidebarTab('chat')
            setDocumentScope('chat')
          }}
          className={`w-full flex items-center gap-2 px-4 py-2.5 text-xs
            font-medium transition-colors border-b border-gray-700
            dark:border-gray-800 relative
            ${isAnalyticsMode
              ? 'bg-indigo-900/40 text-indigo-200 border-l-2 border-l-indigo-500'
              : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
            }`}
        >
          <span>📊</span>
          <span>Analytics</span>
          {isAnalyticsMode && (
            <span className="absolute right-4 w-2 h-2 bg-green-400 rounded-full"/>
          )}
        </button>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto">
          {sidebarTab === 'chat' ? (
            <div className="p-3">
              {/* New Chat button */}
              <button
                onClick={handleNewChat}
                className="w-full flex items-center gap-2 px-3 py-2
                text-sm text-gray-300 hover:bg-gray-700 rounded-lg
                transition-colors border border-gray-600
                hover:border-gray-500 mb-3"
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

              {/* Sessions list */}
              <div className="flex flex-col gap-1">
                {sessions.map(session => (
                  <div
                    key={session.id}
                    className={`group flex items-center gap-2
                      px-3 py-2 rounded-lg cursor-pointer
                      transition-colors text-sm
                      ${activeSessionId === session.id
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                      }`}
                    onClick={() => handleSelectSession(session.id)}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24" fill="currentColor"
                      className="w-3.5 h-3.5 shrink-0">
                      <path fillRule="evenodd" d="M4.848 2.771A49.144
                      49.144 0 0112 2.25c2.43 0 4.817.178 7.152.52
                      1.978.292 3.348 2.024 3.348 3.97v6.02c0
                      1.946-1.37 3.678-3.348 3.97a48.901 48.901
                      0 01-3.476.383.39.39 0 00-.297.17l-2.755
                      4.133a.75.75 0 01-1.248 0l-2.755-4.133a.39.39
                      0 00-.297-.17 48.9 48.9 0 01-3.476-.384c-1.978-.29-3.348-2.024-3.348-3.97V6.741c0-1.946
                      1.37-3.68 3.348-3.97z" clipRule="evenodd" />
                    </svg>
                    <span className="truncate flex-1 text-xs">
                      {session.title}
                    </span>
                    <button
                      onClick={e => {
                        e.stopPropagation()
                        handleDeleteSession(session.id)
                      }}
                      className="opacity-0 group-hover:opacity-100
                      text-gray-500 hover:text-red-400 transition-all"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24" fill="currentColor"
                        className="w-3.5 h-3.5">
                        <path fillRule="evenodd" d="M16.5 4.478v.227a48.816
                        48.816 0 013.878.512.75.75 0 11-.256
                        1.478l-.209-.035-1.005 13.07a3 3 0
                        01-2.991 2.77H8.084a3 3 0
                        01-2.991-2.77L4.087 6.66l-.209.035a.75.75
                        0 01-.256-1.478A48.567 48.567 0 017.5
                        4.705v-.227c0-1.564 1.213-2.9 2.816-2.951a52.662
                        52.662 0 013.369 0c1.603.051 2.815
                        1.387 2.815 2.951zm-6.136-1.452a51.196
                        51.196 0 013.273 0C14.39 3.05 15 3.684
                        15 4.478v.113a49.488 49.488 0
                        00-6 0v-.113c0-.794.609-1.428
                        1.364-1.452zm-.355 5.945a.75.75 0
                        10-1.5.058l.347 9a.75.75 0
                        101.499-.058l-.346-9zm5.48.058a.75.75
                        0 10-1.498-.058l-.347 9a.75.75 0
                        001.5.058l.345-9z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-3">
              <DocumentPanel
                documentScope={documentScope}
                onScopeChange={(scope) => {
                  setDocumentScope(scope)
                  if (scope === 'chat') {
                    setSidebarMode('chat')
                  } else {
                    setSidebarMode('documents')
                  }
                }}
              />
            </div>
          )}
        </div>

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

      {/* Main area */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100
          dark:border-gray-700 bg-white dark:bg-gray-900
          flex items-center justify-between">
          <div>
            <h1 className="text-sm font-medium text-gray-700
              dark:text-gray-200 flex items-center gap-2">
              {isAnalyticsMode ? (
                <>
                  <span>📊</span>
                  <span>Analytics Dashboard</span>
                </>
              ) : isFaqMode ? (
                <>
                  <span>📋</span>
                  <span>Company FAQ</span>
                </>
              ) : isDocumentQueryMode ? (
                <>
                  <span>{documentScope === 'all' ? '📚' : '📄'}</span>
                  <span>
                    {documentScope === 'all'
                      ? 'All Documents'
                      : 'Document Discussion'}
                  </span>
                </>
              ) : (
                activeSession?.title ?? 'New Conversation'
              )}
            </h1>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              {isAnalyticsMode
                ? 'Support conversation metrics and insights.'
                : isFaqMode
                ? 'Ask questions about company policies.'
                : documentScope === 'all'
                ? 'Searching across all your uploaded documents'
                : selectedDocId
                ? 'Asking questions about your document'
                : 'Powered by AI'
              }
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Persona selector — only in chat mode */}
            {!isDocumentQueryMode && !isFaqMode && !isAnalyticsMode && (
              <select
                value={persona}
                onChange={e => setPersona(e.target.value)}
                className="text-xs border border-gray-200
                  dark:border-gray-700 rounded-lg px-2 py-1.5
                  bg-white dark:bg-gray-800 text-gray-700
                  dark:text-gray-200 focus:outline-none
                  focus:ring-2 focus:ring-indigo-500"
              >
                <option value="default">🤖 Default</option>
                <option value="support">🎧 Support</option>
                <option value="code_reviewer">💻 Code Review</option>
                <option value="document_analyst">📄 Doc Analyst</option>
              </select>
            )}

            {/* Dark mode toggle */}
            <button
              onClick={toggleTheme}
              className="text-gray-500 dark:text-gray-400
              hover:text-gray-700 dark:hover:text-gray-200
              transition-colors p-2 rounded-lg
              hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              {theme === 'light' ? (
                <svg xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24" fill="currentColor"
                  className="w-5 h-5">
                  <path fillRule="evenodd" d="M9.528 1.718a.75.75
                  0 01.162.819A8.97 8.97 0 009 6a9 9 0 009
                  9 8.97 8.97 0 003.463-.69.75.75 0
                  01.981.98 10.503 10.503 0 01-9.694
                  6.46c-5.799 0-10.5-4.701-10.5-10.5
                  0-4.368 2.667-8.112 6.46-9.694a.75.75
                  0 01.818.162z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24" fill="currentColor"
                  className="w-5 h-5">
                  <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75
                  0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5
                  4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894
                  6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75
                  0 101.06 1.061l1.591-1.59zM21.75 12a.75.75
                  0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75
                  0 01.75.75zM17.834 18.894a.75.75 0
                  001.06-1.06l-1.59-1.591a.75.75 0
                  10-1.061 1.06l1.59 1.591zM12 18a.75.75
                  0 01.75.75V21a.75.75 0 01-1.5
                  0v-2.25A.75.75 0 0112 18zM7.758
                  17.303a.75.75 0 00-1.061-1.06l-1.591
                  1.59a.75.75 0 001.06 1.061l1.591-1.59zM6
                  12a.75.75 0 01-.75.75H3a.75.75 0
                  010-1.5h2.25A.75.75 0 016 12zM6.697
                  7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75
                  0 00-1.061 1.06l1.59 1.591z" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {isAnalyticsMode ? (
          <AnalyticsDashboard />
        ) : (
          <>
            {isFaqMode && (
              <FaqQuickChips
                onSelect={handleSend}
                disabled={isLoading}
              />
            )}

            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              isFaqMode={isFaqMode}
              onFaqQuestion={handleSend}
              loadingMessage={
                isFaqMode && isLoading ? FAQ_LOADING_MESSAGE : undefined
              }
            />

            <MessageInput
              onSend={handleSend}
              isLoading={isLoading}
              placeholder={
                isFaqMode
                  ? 'Ask about returns, warranty, shipping, cancellation...'
                  : documentScope === 'all'
                  ? 'Ask a question across all your documents...'
                  : selectedDocId
                  ? 'Ask a question about your document...'
                  : undefined
              }
            />
          </>
        )}
      </main>
    </div>
  )
}