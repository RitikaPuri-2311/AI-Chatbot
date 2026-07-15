import type { ChatSession } from '@/types'

export type SessionGroup = 'pinned' | 'today' | 'yesterday' | 'last7' | 'older'

export interface GroupedSessions {
  pinned: ChatSession[]
  today: ChatSession[]
  yesterday: ChatSession[]
  last7: ChatSession[]
  older: ChatSession[]
}

const GROUP_LABELS: Record<Exclude<SessionGroup, 'pinned'>, string> = {
  today: 'Today',
  yesterday: 'Yesterday',
  last7: 'Last 7 Days',
  older: 'Older',
}

export function getGroupLabel(group: Exclude<SessionGroup, 'pinned'>): string {
  return GROUP_LABELS[group]
}

function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}

export function groupSessions(
  sessions: ChatSession[],
  pinnedIds: string[],
): GroupedSessions {
  const now = new Date()
  const todayStart = startOfDay(now)
  const yesterdayStart = new Date(todayStart)
  yesterdayStart.setDate(yesterdayStart.getDate() - 1)
  const last7Start = new Date(todayStart)
  last7Start.setDate(last7Start.getDate() - 7)

  const pinned: ChatSession[] = []
  const today: ChatSession[] = []
  const yesterday: ChatSession[] = []
  const last7: ChatSession[] = []
  const older: ChatSession[] = []

  const pinnedSet = new Set(pinnedIds)

  for (const session of sessions) {
    if (pinnedSet.has(session.id)) {
      pinned.push(session)
      continue
    }

    const created = new Date(session.createdAt)
    const day = startOfDay(created)

    if (day.getTime() >= todayStart.getTime()) {
      today.push(session)
    } else if (day.getTime() >= yesterdayStart.getTime()) {
      yesterday.push(session)
    } else if (day.getTime() >= last7Start.getTime()) {
      last7.push(session)
    } else {
      older.push(session)
    }
  }

  return { pinned, today, yesterday, last7, older }
}

export function filterSessions(
  sessions: ChatSession[],
  query: string,
): ChatSession[] {
  const q = query.trim().toLowerCase()
  if (!q) return sessions
  return sessions.filter(s => s.title.toLowerCase().includes(q))
}
