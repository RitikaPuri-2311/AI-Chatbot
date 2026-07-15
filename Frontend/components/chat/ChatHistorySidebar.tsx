'use client'

import { useState, useEffect, useRef } from 'react'
import {
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  Pin,
  PinOff,
  MessageSquare,
} from 'lucide-react'
import type { ChatSession } from '@/types'
import {
  groupSessions,
  filterSessions,
  getGroupLabel,
  type GroupedSessions,
} from '@/lib/sessionGroups'
import {
  getPinnedSessionIds,
  togglePinSession,
  isSessionPinned,
} from '@/lib/sessionMeta'
import EmptyState from '@/components/ui/EmptyState'
import { SessionListSkeleton } from '@/components/ui/Skeleton'

interface Props {
  sessions: ChatSession[]
  activeSessionId: string
  loading?: boolean
  onNewChat: () => void
  onSelectSession: (id: string) => void
  onDeleteSession: (id: string) => void
  onRenameSession: (id: string, title: string) => void
  onPinChange?: () => void
}

type MenuState = { sessionId: string; x: number; y: number } | null

function SessionRow({
  session,
  isActive,
  isPinned,
  onSelect,
  onOpenMenu,
}: {
  session: ChatSession
  isActive: boolean
  isPinned: boolean
  onSelect: () => void
  onOpenMenu: (e: React.MouseEvent) => void
}) {
  return (
    <div
      className={`group flex items-center gap-1.5 px-2.5 py-2 rounded-xl
        cursor-pointer transition-all duration-150
        ${isActive
          ? 'bg-violet-600/15 border border-violet-500/25 text-violet-200'
          : 'hover:bg-[var(--color-surface-overlay)] text-[var(--color-text-secondary)] border border-transparent'
        }`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect()
        }
      }}
      aria-current={isActive ? 'true' : undefined}
    >
      {isPinned ? (
        <Pin className="w-3 h-3 shrink-0 text-violet-400" aria-hidden />
      ) : (
        <MessageSquare className="w-3 h-3 shrink-0 opacity-50" aria-hidden />
      )}
      <span className="truncate flex-1 text-xs font-medium">
        {session.title}
      </span>
      <button
        type="button"
        onClick={e => {
          e.stopPropagation()
          onOpenMenu(e)
        }}
        className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100
          p-1 rounded-lg text-[var(--color-text-muted)]
          hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-overlay)]
          transition-all focus:opacity-100"
        aria-label={`Options for ${session.title}`}
      >
        <MoreHorizontal className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}

function SessionGroup({
  label,
  sessions,
  activeSessionId,
  pinnedIds,
  onSelect,
  onOpenMenu,
}: {
  label: string
  sessions: ChatSession[]
  activeSessionId: string
  pinnedIds: string[]
  onSelect: (id: string) => void
  onOpenMenu: (sessionId: string, e: React.MouseEvent) => void
}) {
  if (sessions.length === 0) return null

  return (
    <div className="mb-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider
        text-[var(--color-text-muted)] px-2 mb-1.5">
        {label}
      </p>
      <div className="flex flex-col gap-0.5">
        {sessions.map(session => (
          <SessionRow
            key={session.id}
            session={session}
            isActive={activeSessionId === session.id}
            isPinned={pinnedIds.includes(session.id)}
            onSelect={() => onSelect(session.id)}
            onOpenMenu={e => onOpenMenu(session.id, e)}
          />
        ))}
      </div>
    </div>
  )
}

export default function ChatHistorySidebar({
  sessions,
  activeSessionId,
  loading,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onRenameSession,
  onPinChange,
}: Props) {
  const [search, setSearch] = useState('')
  const [pinnedIds, setPinnedIds] = useState<string[]>([])
  const [menu, setMenu] = useState<MenuState>(null)
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPinnedIds(getPinnedSessionIds())
  }, [sessions])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenu(null)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const filtered = filterSessions(sessions, search)
  const grouped: GroupedSessions = groupSessions(filtered, pinnedIds)

  function handleOpenMenu(sessionId: string, e: React.MouseEvent) {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setMenu({ sessionId, x: rect.right, y: rect.bottom })
  }

  function handlePin(sessionId: string) {
    togglePinSession(sessionId)
    setPinnedIds(getPinnedSessionIds())
    onPinChange?.()
    setMenu(null)
  }

  function handleStartRename(sessionId: string) {
    const session = sessions.find(s => s.id === sessionId)
    setRenaming(sessionId)
    setRenameValue(session?.title ?? '')
    setMenu(null)
  }

  function handleConfirmRename() {
    if (renaming && renameValue.trim()) {
      onRenameSession(renaming, renameValue.trim())
    }
    setRenaming(null)
    setRenameValue('')
  }

  const timeGroups: Array<{ key: keyof GroupedSessions; label: string }> = [
    { key: 'today', label: getGroupLabel('today') },
    { key: 'yesterday', label: getGroupLabel('yesterday') },
    { key: 'last7', label: getGroupLabel('last7') },
    { key: 'older', label: getGroupLabel('older') },
  ]

  return (
    <div className="flex flex-col h-full gap-2">
      {/* Search */}
      <div className="relative">
        <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2
          text-[var(--color-text-muted)] pointer-events-none" aria-hidden />
        <input
          type="search"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search chats"
          aria-label="Search chats"
          className="w-full pl-9 pr-3 py-2 text-xs rounded-xl
            bg-[var(--color-surface-overlay)] border border-[var(--color-border-subtle)]
            text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)]
            focus:outline-none focus:ring-2 focus:ring-violet-500/30
            focus:border-violet-500/40 transition-all"
        />
      </div>

      {/* New Chat */}
      <button
        type="button"
        onClick={onNewChat}
        className="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl
          text-sm font-medium text-[var(--color-text-primary)]
          bg-violet-600/15 border border-violet-500/25
          hover:bg-violet-600/25 hover:border-violet-500/40
          transition-all duration-200"
      >
        <Plus className="w-4 h-4 text-violet-400" aria-hidden />
        New Chat
      </button>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto min-h-0 -mx-1 px-1">
        {loading ? (
          <SessionListSkeleton />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={MessageSquare}
            title={search ? 'No matching chats' : 'No chats yet'}
            description={search ? 'Try a different search term' : 'Start a new conversation'}
          />
        ) : (
          <>
            {renaming && (
              <div className="mb-2 px-1">
                <input
                  autoFocus
                  value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleConfirmRename()
                    if (e.key === 'Escape') setRenaming(null)
                  }}
                  onBlur={handleConfirmRename}
                  className="w-full px-2 py-1.5 text-xs rounded-lg
                    bg-[var(--color-surface-overlay)] border border-violet-500/40
                    text-[var(--color-text-primary)] focus:outline-none"
                  aria-label="Rename chat"
                />
              </div>
            )}

            <SessionGroup
              label="Pinned"
              sessions={grouped.pinned}
              activeSessionId={activeSessionId}
              pinnedIds={pinnedIds}
              onSelect={onSelectSession}
              onOpenMenu={handleOpenMenu}
            />

            {timeGroups.map(({ key, label }) => (
              <SessionGroup
                key={key}
                label={label}
                sessions={grouped[key]}
                activeSessionId={activeSessionId}
                pinnedIds={pinnedIds}
                onSelect={onSelectSession}
                onOpenMenu={handleOpenMenu}
              />
            ))}
          </>
        )}
      </div>

      {/* Context menu */}
      {menu && (
        <div
          ref={menuRef}
          role="menu"
          className="fixed z-50 min-w-[140px] py-1 rounded-xl
            bg-[var(--color-surface-raised)] border border-[var(--color-border-subtle)]
            shadow-xl shadow-black/20 animate-fade-in"
          style={{ top: menu.y + 4, left: Math.min(menu.x - 140, window.innerWidth - 160) }}
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => handleStartRename(menu.sessionId)}
            className="flex items-center gap-2 w-full px-3 py-2 text-xs
              text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-overlay)]
              transition-colors"
          >
            <Pencil className="w-3.5 h-3.5" />
            Rename
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              handlePin(menu.sessionId)
            }}
            className="flex items-center gap-2 w-full px-3 py-2 text-xs
              text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-overlay)]
              transition-colors"
          >
            {isSessionPinned(menu.sessionId) ? (
              <>
                <PinOff className="w-3.5 h-3.5" />
                Unpin
              </>
            ) : (
              <>
                <Pin className="w-3.5 h-3.5" />
                Pin
              </>
            )}
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              onDeleteSession(menu.sessionId)
              setMenu(null)
            }}
            className="flex items-center gap-2 w-full px-3 py-2 text-xs
              text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </button>
        </div>
      )}
    </div>
  )
}
