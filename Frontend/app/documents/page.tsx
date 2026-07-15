'use client'

import { useState, useEffect, useRef } from 'react'
import {
  Upload,
  FileText,
  Trash2,
  Loader2,
  Clock,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import AppShell from '@/components/layout/AppShell'
import PageHeader from '@/components/layout/PageHeader'
import ChatWindow from '@/components/chat/ChatWindow'
import MessageInput from '@/components/chat/MessageInput'
import EmptyState from '@/components/ui/EmptyState'
import { DocumentListSkeleton } from '@/components/ui/Skeleton'
import { uploadDocument, getDocuments, deleteDocument, queryDocuments } from '@/lib/api'
import { formatUploadTime } from '@/lib/formatTime'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import type { Message, Document, Source } from '@/types'

const DOC_SUGGESTED_PROMPTS = [
  { title: 'Summarize', prompt: 'Summarize the key points from this document.' },
  { title: 'Find details', prompt: 'What are the main topics covered in this document?' },
  { title: 'Key dates', prompt: 'List all important dates and deadlines mentioned.' },
  { title: 'Explain', prompt: 'Explain the most important concepts in simple terms.' },
] as const

export default function DocumentsPage() {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingDocs, setIsLoadingDocs] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const pollingRef = useRef<NodeJS.Timeout[]>([])
  const [sessionId] = useState(() => `doc-${Date.now()}`)

  const selectedDoc = documents.find(d => d.id === selectedDocId)
  const indexedDocs = documents.filter(d => d.status === 'indexed')
  const recentDocs = [...indexedDocs]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  async function loadDocuments() {
    setIsLoadingDocs(true)
    const data = await getDocuments()
    setDocuments(data as Document[])
    setIsLoadingDocs(false)
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDocuments()
    const timers = pollingRef.current
    return () => { timers.forEach(clearInterval) }
  }, [])

  function selectDocument(docId: string) {
    setSelectedDocId(docId)
    setMessages([])
  }

  async function handleUpload(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Only PDF files are supported')
      return
    }

    setUploading(true)
    try {
      const data = await uploadDocument(file) as { document_id: string }
      toast.success(`${file.name} uploaded — indexing...`)

      const newDoc: Document = {
        id: data.document_id,
        filename: file.name,
        status: 'processing',
        chunk_count: 0,
        page_count: 0,
        created_at: new Date().toISOString(),
      }
      setDocuments(prev => [newDoc, ...prev])
      startPolling(data.document_id, file.name)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  function startPolling(docId: string, filename: string) {
    const interval = setInterval(async () => {
      const data = await getDocuments() as Document[]
      const doc = data.find(d => d.id === docId)
      if (doc?.status === 'indexed') {
        setDocuments(data)
        toast.success(`${filename} ready`)
        clearInterval(interval)
      } else if (doc?.status === 'failed') {
        setDocuments(data)
        toast.error(`Failed to index ${filename}`)
        clearInterval(interval)
      }
    }, 2000)
    pollingRef.current.push(interval)
    setTimeout(() => clearInterval(interval), 120000)
  }

  async function handleDelete(docId: string, filename: string) {
    const ok = await deleteDocument(docId)
    if (!ok) {
      toast.error('Delete failed')
      return
    }
    setDocuments(prev => prev.filter(d => d.id !== docId))
    if (selectedDocId === docId) setSelectedDocId(null)
    toast.success(`${filename} deleted`)
  }

  function triggerUpload() {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.pdf'
    input.onchange = e => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) handleUpload(file)
    }
    input.click()
  }

  async function handleSend(content: string) {
    if (!selectedDocId) {
      toast.error('Select a document first')
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    const aiMessageId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, {
      id: aiMessageId,
      role: 'assistant',
      content: '🔍 Searching document...',
      createdAt: new Date().toISOString(),
    }])

    try {
      const result = await queryDocuments(content, selectedDocId, sessionId)
      setMessages(prev => prev.map(msg =>
        msg.id === aiMessageId
          ? { ...msg, content: result.answer, sources: result.sources as Source[] }
          : msg,
      ))
    } catch {
      toast.error('Something went wrong. Please try again.')
      setMessages(prev => prev.map(msg =>
        msg.id === aiMessageId
          ? { ...msg, content: 'Something went wrong. Please try again.' }
          : msg,
      ))
    } finally {
      setIsLoading(false)
    }
  }

  function StatusIcon({ status }: { status: string }) {
    switch (status) {
      case 'indexed':
        return <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-3.5 h-3.5 text-red-400" />
      default:
        return <Clock className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
    }
  }

  function DocRow({ doc }: { doc: Document }) {
    const isSelected = selectedDocId === doc.id
    const canSelect = doc.status === 'indexed'

    return (
      <div
        role="button"
        tabIndex={canSelect ? 0 : -1}
        onClick={() => canSelect && selectDocument(doc.id)}
        onKeyDown={e => {
          if (canSelect && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault()
            selectDocument(doc.id)
          }
        }}
        className={`group flex items-start gap-2.5 px-3 py-3 rounded-2xl
          transition-all duration-150
          ${isSelected
            ? 'bg-violet-600/15 border border-violet-500/25'
            : canSelect
            ? 'hover:bg-[var(--color-surface-overlay)] border border-transparent cursor-pointer'
            : 'opacity-60 border border-transparent'
          }`}
        aria-current={isSelected ? 'true' : undefined}
      >
        <StatusIcon status={doc.status} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-[var(--color-text-primary)] truncate">
            {doc.filename}
          </p>
          <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
            {doc.status === 'indexed'
              ? `${formatUploadTime(doc.created_at)} · ${doc.page_count}p`
              : doc.status === 'processing'
              ? 'Indexing...'
              : 'Failed'}
          </p>
        </div>
        {doc.status !== 'processing' && (
          <button
            type="button"
            onClick={e => {
              e.stopPropagation()
              handleDelete(doc.id, doc.filename)
            }}
            aria-label={`Delete ${doc.filename}`}
            className="opacity-0 group-hover:opacity-100 p-1 rounded-lg
              text-[var(--color-text-muted)] hover:text-red-400
              hover:bg-red-500/10 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    )
  }

  return (
    <AppShell
      header={
        <PageHeader
          title="Document Chat"
          subtitle={
            selectedDoc
              ? `Chatting with: ${selectedDoc.filename}`
              : 'Select a document to start'
          }
          icon={<FileText className="w-4 h-4 text-violet-500" />}
          user={user}
        />
      }
    >
      <div className="flex flex-1 min-h-0">
        {/* Library panel */}
        <div className="w-80 shrink-0 border-r border-[var(--color-border-subtle)]
          bg-[var(--color-surface-raised)] flex flex-col overflow-hidden
          hidden md:flex">
          <div className="p-4 border-b border-[var(--color-border-subtle)]">
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={e => {
                e.preventDefault()
                setDragOver(false)
                const file = e.dataTransfer.files[0]
                if (file) handleUpload(file)
              }}
              onClick={triggerUpload}
              className={`border-2 border-dashed rounded-2xl p-5 text-center
                cursor-pointer transition-all duration-200
                ${dragOver
                  ? 'border-violet-500 bg-violet-600/10'
                  : 'border-[var(--color-border-subtle)] hover:border-violet-500/40 hover:bg-violet-600/5'
                }
                ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
            >
              {uploading ? (
                <Loader2 className="w-6 h-6 text-violet-500 mx-auto mb-2 animate-spin" />
              ) : (
                <Upload className="w-6 h-6 text-violet-500 mx-auto mb-2" />
              )}
              <p className="text-xs font-medium text-[var(--color-text-secondary)]">
                {uploading ? 'Uploading...' : 'Drop PDF or click to upload'}
              </p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3">
            {isLoadingDocs ? (
              <DocumentListSkeleton />
            ) : documents.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No documents"
                description="Upload a PDF to start asking questions with citations"
              />
            ) : (
              <>
                {recentDocs.length > 0 && (
                  <section className="mb-4">
                    <p className="text-[10px] font-semibold uppercase tracking-wider
                      text-[var(--color-text-muted)] px-2 mb-2">
                      Recent Documents
                    </p>
                    <div className="flex flex-col gap-1">
                      {recentDocs.map(doc => <DocRow key={doc.id} doc={doc} />)}
                    </div>
                  </section>
                )}

                <section>
                  <p className="text-[10px] font-semibold uppercase tracking-wider
                    text-[var(--color-text-muted)] px-2 mb-2">
                    All Documents
                  </p>
                  <div className="flex flex-col gap-1">
                    {documents.map(doc => <DocRow key={`all-${doc.id}`} doc={doc} />)}
                  </div>
                </section>
              </>
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="md:hidden px-4 py-2 border-b border-[var(--color-border-subtle)]
            flex gap-2">
            <button
              type="button"
              onClick={triggerUpload}
              disabled={uploading}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs
                font-medium bg-violet-600/15 text-violet-600 dark:text-violet-300
                border border-violet-500/25"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload
            </button>
            {indexedDocs.length > 0 && (
              <select
                value={selectedDocId ?? ''}
                onChange={e => selectDocument(e.target.value)}
                aria-label="Select document"
                className="flex-1 text-xs px-2 py-1.5 rounded-xl
                  bg-[var(--color-surface-raised)] border
                  border-[var(--color-border-subtle)]"
              >
                <option value="" disabled>Select document</option>
                {indexedDocs.map(d => (
                  <option key={d.id} value={d.id}>{d.filename}</option>
                ))}
              </select>
            )}
          </div>

          {!selectedDocId ? (
            <EmptyState
              icon={FileText}
              title="Select a document"
              description="Choose a document from the library to start a dedicated chat with citations"
            />
          ) : (
            <>
              <ChatWindow
                messages={messages}
                isLoading={isLoading}
                suggestedPrompts={DOC_SUGGESTED_PROMPTS}
                onSuggestedPrompt={handleSend}
                loadingMessage="🔍 Searching document..."
              />
              <MessageInput
                onSend={handleSend}
                isLoading={isLoading}
                showAttach={false}
                placeholder={`Ask about ${selectedDoc?.filename ?? 'this document'}...`}
              />
            </>
          )}
        </div>
      </div>
    </AppShell>
  )
}
