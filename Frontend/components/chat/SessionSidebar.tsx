'use client'
import { ChatSession } from '@/types'

interface Props {
  sessions: ChatSession[]
  activeSessionId: string
  onSelectSession: (id: string) => void
  onNewChat: () => void
  onDeleteSession: (id: string) => void
  username: string
  onLogout: () => void
}

export default function SessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  username,
  onLogout
}: Props) {
  return (
    <aside className="w-64 bg-gray-900 dark:bg-gray-950 
      flex flex-col shrink-0">

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
          onClick={onNewChat}
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

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto px-3 pt-3">
        {sessions.length === 0 ? (
          <p className="text-xs text-gray-500 px-2 py-4 text-center">
            No conversations yet
          </p>
        ) : (
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
                onClick={() => onSelectSession(session.id)}
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
                    onDeleteSession(session.id)
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
        )}
      </div>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-gray-700">
        <div className="flex items-center gap-3 px-2 py-2
          rounded-lg hover:bg-gray-700 transition-colors">
          <div className="w-7 h-7 bg-indigo-600 rounded-full
            flex items-center justify-center text-xs
            font-semibold text-white shrink-0">
            {username?.charAt(0).toUpperCase() ?? 'U'}
          </div>
          <span className="text-sm text-gray-300 truncate flex-1">
            {username ?? 'User'}
          </span>
          <button
            onClick={onLogout}
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
  )
}