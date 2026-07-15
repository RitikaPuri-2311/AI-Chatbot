'use client'

import { createContext, useContext, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import AppSidebar from '@/components/layout/AppSidebar'
import LoadingScreen from '@/components/layout/LoadingScreen'

interface ShellContextValue {
  openMenu: () => void
  closeMenu: () => void
}

const ShellContext = createContext<ShellContextValue>({
  openMenu: () => {},
  closeMenu: () => {},
})

export function useAppShell() {
  return useContext(ShellContext)
}

interface Props {
  children: React.ReactNode
  sidebarContent?: React.ReactNode
  header?: React.ReactNode
}

export default function AppShell({ children, sidebarContent, header }: Props) {
  const { user, loading } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  if (loading) {
    return <LoadingScreen />
  }

  return (
    <ShellContext.Provider
      value={{
        openMenu: () => setMobileOpen(true),
        closeMenu: () => setMobileOpen(false),
      }}
    >
      <div className="flex h-screen overflow-hidden bg-[var(--color-surface)]">
        <AppSidebar
          user={user}
          sidebarContent={sidebarContent}
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed(c => !c)}
        />

        <div className="flex-1 flex flex-col min-w-0">
          {header}
          <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {children}
          </main>
        </div>
      </div>
    </ShellContext.Provider>
  )
}
