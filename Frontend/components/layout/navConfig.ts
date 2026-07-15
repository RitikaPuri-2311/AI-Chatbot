import {
  MessageSquare,
  FileText,
  HelpCircle,
  LifeBuoy,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  label: string
  href: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'AI Chat', href: '/chat', icon: MessageSquare },
  { label: 'Document Chat', href: '/documents', icon: FileText },
  { label: 'Company FAQ', href: '/faq', icon: HelpCircle },
  { label: 'Help & Support', href: '/help-support', icon: LifeBuoy },
]
