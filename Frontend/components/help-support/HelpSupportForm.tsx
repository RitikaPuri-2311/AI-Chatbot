'use client'

import { useState } from 'react'
import { Paperclip, Loader2 } from 'lucide-react'
import IssueTypeCard from '@/components/help-support/IssueTypeCard'
import SuccessMessage from '@/components/help-support/SuccessMessage'
import {
  QUICK_ACTIONS,
  SUPPORT_ISSUE_TYPES,
  SUPPORT_PRIORITIES,
  buildSupportDescription,
  toBackendIssueType,
  type QuickAction,
  type SupportIssueType,
  type SupportPriority,
} from '@/components/help-support/helpSupportConfig'
import { submitSupportRequest } from '@/lib/api'
import toast from 'react-hot-toast'

interface FormErrors {
  issueType?: string
  summary?: string
  description?: string
}

const INITIAL_FORM = {
  issueType: '' as SupportIssueType | '',
  summary: '',
  description: '',
  priority: 'Medium' as SupportPriority,
}

const inputClass = `w-full rounded-2xl border border-[var(--color-border-subtle)]
  px-4 py-2.5 text-sm bg-[var(--color-surface-raised)]
  text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)]
  focus:outline-none focus:ring-2 focus:ring-violet-500/30
  focus:border-violet-500/40 transition-all`

export default function HelpSupportForm() {
  const [form, setForm] = useState(INITIAL_FORM)
  const [errors, setErrors] = useState<FormErrors>({})
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [referenceKey, setReferenceKey] = useState<string | null>(null)
  const [ticketUrl, setTicketUrl] = useState<string | undefined>()

  function handleQuickAction(action: QuickAction) {
    setSelectedActionId(action.id)
    setForm(prev => ({
      ...prev,
      issueType: action.issueType,
      summary: prev.summary || action.summaryHint,
      description: action.id === 'human'
        ? prev.description || 'I would like to speak with a human support agent.'
        : prev.description,
    }))
    setErrors({})
    setSubmitError(null)
  }

  function validate(): boolean {
    const next: FormErrors = {}
    if (!form.issueType) next.issueType = 'Please select a category.'
    if (!form.summary.trim()) next.summary = 'Subject is required.'
    if (!form.description.trim()) next.description = 'Description is required.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  function handleCancel() {
    setForm(INITIAL_FORM)
    setErrors({})
    setSubmitError(null)
    setSelectedActionId(null)
    setReferenceKey(null)
    setTicketUrl(undefined)
  }

  function handleCreateAnother() {
    handleCancel()
  }

  function handleAttach() {
    toast('File attachments coming soon', { icon: '📎' })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitError(null)
    if (!validate()) return

    setIsSubmitting(true)
    try {
      const issueType = form.issueType as SupportIssueType
      const result = await submitSupportRequest({
        summary: form.summary.trim(),
        description: buildSupportDescription(
          form.description,
          form.priority,
          issueType,
        ),
        issue_type: toBackendIssueType(issueType),
      })

      if (!result.success || !result.key) {
        setSubmitError(result.message ?? 'Unable to submit your request. Please try again.')
        return
      }

      setReferenceKey(result.key)
      setTicketUrl(result.self_url)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : ''
      if (
        message.toLowerCase().includes('fetch') ||
        message.toLowerCase().includes('network') ||
        message.toLowerCase().includes('unavailable')
      ) {
        setSubmitError('The server is currently unavailable. Please try again later.')
      } else {
        setSubmitError(message || 'Unable to submit your request. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (referenceKey) {
    return (
      <SuccessMessage
        referenceKey={referenceKey}
        ticketUrl={ticketUrl}
        onCreateAnother={handleCreateAnother}
      />
    )
  }

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">
          How can we help?
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {QUICK_ACTIONS.map(action => (
            <IssueTypeCard
              key={action.id}
              action={action}
              selected={selectedActionId === action.id}
              onSelect={handleQuickAction}
            />
          ))}
        </div>
      </section>

      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {submitError && (
          <div role="alert" className="rounded-2xl border border-red-500/25
            bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {submitError}
          </div>
        )}

        <div>
          <label htmlFor="issueType" className="block text-sm font-medium
            text-[var(--color-text-secondary)] mb-1.5">
            Category <span className="text-red-400">*</span>
          </label>
          <select
            id="issueType"
            value={form.issueType}
            onChange={e => {
              setForm(prev => ({ ...prev, issueType: e.target.value as SupportIssueType }))
              setErrors(prev => ({ ...prev, issueType: undefined }))
              setSelectedActionId(null)
            }}
            className={`${inputClass} ${errors.issueType ? 'border-red-400' : ''}`}
          >
            <option value="">Select category</option>
            {SUPPORT_ISSUE_TYPES.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          {errors.issueType && <p className="mt-1 text-xs text-red-400">{errors.issueType}</p>}
        </div>

        <div>
          <label htmlFor="summary" className="block text-sm font-medium
            text-[var(--color-text-secondary)] mb-1.5">
            Subject <span className="text-red-400">*</span>
          </label>
          <input
            id="summary"
            type="text"
            value={form.summary}
            onChange={e => {
              setForm(prev => ({ ...prev, summary: e.target.value }))
              setErrors(prev => ({ ...prev, summary: undefined }))
            }}
            maxLength={255}
            placeholder="Brief summary of your issue"
            className={`${inputClass} ${errors.summary ? 'border-red-400' : ''}`}
          />
          {errors.summary && <p className="mt-1 text-xs text-red-400">{errors.summary}</p>}
        </div>

        <div>
          <label htmlFor="priority" className="block text-sm font-medium
            text-[var(--color-text-secondary)] mb-1.5">
            Priority
          </label>
          <select
            id="priority"
            value={form.priority}
            onChange={e => setForm(prev => ({
              ...prev,
              priority: e.target.value as SupportPriority,
            }))}
            className={inputClass}
          >
            {SUPPORT_PRIORITIES.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium
            text-[var(--color-text-secondary)] mb-1.5">
            Description <span className="text-red-400">*</span>
          </label>
          <textarea
            id="description"
            value={form.description}
            onChange={e => {
              setForm(prev => ({ ...prev, description: e.target.value }))
              setErrors(prev => ({ ...prev, description: undefined }))
            }}
            rows={5}
            maxLength={5000}
            placeholder="Please describe your issue in detail..."
            className={`${inputClass} resize-y ${errors.description ? 'border-red-400' : ''}`}
          />
          {errors.description && (
            <p className="mt-1 text-xs text-red-400">{errors.description}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5">
            Attachments
          </label>
          <button
            type="button"
            onClick={handleAttach}
            className="flex items-center gap-2 px-4 py-3 rounded-2xl border
              border-dashed border-[var(--color-border-subtle)]
              text-sm text-[var(--color-text-muted)]
              hover:border-violet-500/40 hover:bg-violet-600/5 transition-all w-full"
          >
            <Paperclip className="w-4 h-4" />
            Attach files (coming soon)
          </button>
        </div>

        <div className="flex flex-col-reverse sm:flex-row gap-3 pt-2">
          <button
            type="button"
            onClick={handleCancel}
            disabled={isSubmitting}
            className="px-5 py-2.5 text-sm font-medium rounded-2xl
              border border-[var(--color-border-subtle)]
              text-[var(--color-text-secondary)]
              hover:bg-[var(--color-surface-overlay)]
              disabled:opacity-50 transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2.5 text-sm font-medium rounded-2xl
              bg-gradient-to-r from-violet-600 to-indigo-600 text-white
              hover:from-violet-500 hover:to-indigo-500
              disabled:opacity-60 disabled:cursor-not-allowed
              transition-all flex items-center justify-center gap-2
              shadow-sm shadow-violet-900/20"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            {isSubmitting ? 'Submitting...' : 'Submit Ticket'}
          </button>
        </div>
      </form>
    </div>
  )
}
