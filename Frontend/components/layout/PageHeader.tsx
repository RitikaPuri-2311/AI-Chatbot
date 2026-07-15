'use client'

import type { ReactNode } from 'react'
import { ThemeToggle } from '@/components/ThemeProvider'
import { MobileMenuButton } from '@/components/layout/AppSidebar'
import { useAppShell } from '@/components/layout/AppShell'
import type { User } from '@/types'

interface Props {
  title: string
  subtitle?: string
  icon?: ReactNode
  actions?: ReactNode
  user?: User | null
}

export default function PageHeader({ title, subtitle, icon, actions, user }: Props) {
  const { openMenu } = useAppShell()

  return (
    <header className="shrink-0 px-4 sm:px-5 py-3 border-b border-[var(--color-border-subtle)]
      bg-[var(--color-surface)]/90 backdrop-blur-sm flex items-center justify-between gap-3">
      <div className="flex items-center gap-3 min-w-0">
        <MobileMenuButton onClick={openMenu} />
        {icon && (
          <div className="w-9 h-9 rounded-2xl bg-violet-600/10 border
            border-violet-500/20 flex items-center justify-center shrink-0 hidden sm:flex">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <h1 className="text-sm font-semibold text-[var(--color-text-primary)] truncate">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-[var(--color-text-muted)] truncate hidden sm:block">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {actions}
        <ThemeToggle />
        {user && (
          <div
            className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500
              to-indigo-600 flex items-center justify-center text-xs font-semibold
              text-white shrink-0 hidden sm:flex"
            title={user.username}
            aria-label={`Signed in as ${user.username}`}
          >
            {user.username.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  )
}
