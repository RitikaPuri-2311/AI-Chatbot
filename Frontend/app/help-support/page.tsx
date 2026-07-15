'use client'

import { LifeBuoy } from 'lucide-react'
import AppShell from '@/components/layout/AppShell'
import PageHeader from '@/components/layout/PageHeader'
import HelpSupportForm from '@/components/help-support/HelpSupportForm'
import { useAuth } from '@/hooks/useAuth'

export default function HelpSupportPage() {
  const { user } = useAuth()

  return (
    <AppShell
      header={
        <PageHeader
          title="Help & Support"
          subtitle="Submit a ticket and our team will get back to you"
          icon={<LifeBuoy className="w-4 h-4 text-violet-500" />}
          user={user}
        />
      }
    >
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 sm:py-8">
        <div className="max-w-3xl mx-auto">
          <HelpSupportForm />
        </div>
      </div>
    </AppShell>
  )
}
