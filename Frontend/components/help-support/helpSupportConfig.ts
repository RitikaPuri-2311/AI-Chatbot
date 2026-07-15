export type SupportIssueType = 'Bug' | 'Support' | 'Payment' | 'Order' | 'Technical'

export type SupportPriority = 'Low' | 'Medium' | 'High'

export interface QuickAction {
  id: string
  label: string
  emoji: string
  issueType: SupportIssueType
  summaryHint: string
}

export const SUPPORT_ISSUE_TYPES: SupportIssueType[] = [
  'Bug',
  'Support',
  'Payment',
  'Order',
  'Technical',
]

export const SUPPORT_PRIORITIES: SupportPriority[] = [
  'Low',
  'Medium',
  'High',
]

export const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'bug',
    label: 'Report a Bug',
    emoji: '🐞',
    issueType: 'Bug',
    summaryHint: 'Bug report',
  },
  {
    id: 'ticket',
    label: 'Raise a Support Ticket',
    emoji: '🎫',
    issueType: 'Support',
    summaryHint: 'Support request',
  },
  {
    id: 'order',
    label: 'Order Issue',
    emoji: '📦',
    issueType: 'Order',
    summaryHint: 'Order issue',
  },
  {
    id: 'payment',
    label: 'Payment Issue',
    emoji: '💳',
    issueType: 'Payment',
    summaryHint: 'Payment issue',
  },
  {
    id: 'human',
    label: 'Talk to a Human Agent',
    emoji: '👨‍💻',
    issueType: 'Support',
    summaryHint: 'Request to speak with a human agent',
  },
]

/** Maps UI issue types to backend issue type names (internal only). */
export function toBackendIssueType(issueType: SupportIssueType): string {
  if (issueType === 'Bug') return 'Bug'
  return 'Task'
}

export function buildSupportDescription(
  description: string,
  priority: SupportPriority,
  issueType: SupportIssueType,
): string {
  return [
    `Category: ${issueType}`,
    `Priority: ${priority}`,
    '',
    description.trim(),
  ].join('\n')
}
