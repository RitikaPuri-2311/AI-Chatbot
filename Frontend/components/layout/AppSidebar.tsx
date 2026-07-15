'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
  Sparkles,
  Menu,
  X,
} from 'lucide-react'
import { logout } from '@/lib/auth'
import { NAV_ITEMS } from '@/components/layout/navConfig'
import type { User } from '@/types'

interface Props {
  user: User | null
  sidebarContent?: React.ReactNode
  mobileOpen: boolean
  onMobileClose: () => void
  collapsed: boolean
  onToggleCollapse: () => void
}

export default function AppSidebar({
  user,
  sidebarContent,
  mobileOpen,
  onMobileClose,
  collapsed,
  onToggleCollapse,
}: Props) {
  const pathname = usePathname()

  const sidebarInner = (
    <>
      <div className={`flex items-center gap-3 px-4 py-4 border-b
        border-[var(--color-border-subtle)]
        ${collapsed ? 'justify-center px-2' : ''}`}>
        <Link href="/chat" className="flex items-center gap-3 min-w-0" onClick={onMobileClose}>
          <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-violet-600
            to-indigo-600 flex items-center justify-center shrink-0
            shadow-lg shadow-violet-900/25">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-semibold text-[var(--color-text-primary)] truncate">
                AI Chatbot
              </p>
              <p className="text-[10px] text-[var(--color-text-muted)]">
                Powered by Gemini
              </p>
            </div>
          )}
        </Link>
        <button
          type="button"
          onClick={onMobileClose}
          className="ml-auto lg:hidden p-1.5 rounded-lg text-[var(--color-text-muted)]
            hover:bg-[var(--color-surface-overlay)]"
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <nav className="px-3 py-3 flex flex-col gap-0.5" aria-label="Main navigation">
        {NAV_ITEMS.map(item => {
          const isActive =
            pathname === item.href ||
            (item.href !== '/chat' && pathname.startsWith(item.href))
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onMobileClose}
              title={collapsed ? item.label : undefined}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-2xl text-sm
                font-medium transition-all duration-200
                ${collapsed ? 'justify-center px-2' : ''}
                ${isActive
                  ? 'bg-violet-600/15 text-violet-600 dark:text-violet-300 border border-violet-500/25'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-overlay)] border border-transparent'
                }`}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-violet-500 dark:text-violet-400' : ''}`} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {sidebarContent && !collapsed && (
        <div className="flex-1 overflow-y-auto px-3 py-2 min-h-0 border-t
          border-[var(--color-border-subtle)]">
          {sidebarContent}
        </div>
      )}

      {!sidebarContent && <div className="flex-1" />}

      <div className="hidden lg:block px-3 pb-2">
        <button
          type="button"
          onClick={onToggleCollapse}
          className={`flex items-center gap-2 w-full px-2.5 py-2 rounded-xl
            text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]
            hover:bg-[var(--color-surface-overlay)] transition-all text-xs
            ${collapsed ? 'justify-center' : ''}`}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : (
            <>
              <PanelLeftClose className="w-4 h-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>

      <div className={`p-3 border-t border-[var(--color-border-subtle)]
        ${collapsed ? 'flex justify-center' : ''}`}>
        <div className={`flex items-center gap-3 p-2 rounded-2xl
          hover:bg-[var(--color-surface-overlay)] transition-colors w-full
          ${collapsed ? 'justify-center p-2' : ''}`}>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500
            to-indigo-600 flex items-center justify-center text-xs font-semibold
            text-white shrink-0" aria-hidden>
            {user?.username?.charAt(0).toUpperCase() ?? 'U'}
          </div>
          {!collapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                  {user?.username ?? 'User'}
                </p>
                <p className="text-[10px] text-[var(--color-text-muted)] truncate">
                  {user?.email ?? ''}
                </p>
              </div>
              <button
                type="button"
                onClick={logout}
                aria-label="Logout"
                className="p-1.5 rounded-xl text-[var(--color-text-muted)]
                  hover:text-red-400 hover:bg-red-500/10 transition-all"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </>
  )

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onMobileClose}
          aria-hidden
        />
      )}

      <aside
        className={`flex flex-col shrink-0 h-full bg-[var(--color-surface-raised)]
          border-r border-[var(--color-border-subtle)] transition-all duration-300
          fixed lg:relative inset-y-0 left-0 z-50 lg:z-auto
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${collapsed ? 'w-[68px] lg:w-[68px]' : 'w-72'}`}
        aria-label="Sidebar"
      >
        {sidebarInner}
      </aside>
    </>
  )
}

export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="lg:hidden p-2 rounded-xl text-[var(--color-text-muted)]
        hover:bg-[var(--color-surface-overlay)] transition-all"
      aria-label="Open menu"
    >
      <Menu className="w-5 h-5" />
    </button>
  )
}
