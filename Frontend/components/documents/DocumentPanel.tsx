'use client'
import { useState, useEffect, useRef } from 'react'
import { getToken } from '@/lib/auth'
import toast from 'react-hot-toast'
import type { Document } from '@/types'

/** 'chat' = normal chat; 'all' = multi-document search; string = single document id */
export type DocumentScope = 'chat' | 'all' | string

interface Props {
  documentScope: DocumentScope
  onScopeChange: (scope: DocumentScope) => void
}

const API_URL = 'http://localhost:8000'

export default function DocumentPanel({
  documentScope,
  onScopeChange,
}: Props) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const pollingRef = useRef<NodeJS.Timeout[]>([])

  const isAllDocumentsSelected = documentScope === 'all'
  const selectedDocId =
    documentScope !== 'chat' && documentScope !== 'all'
      ? documentScope
      : null

  useEffect(() => {
    loadDocuments()
    return () => {
      pollingRef.current.forEach(clearInterval)
    }
  }, [])

  async function loadDocuments() {
    try {
      const res = await fetch(`${API_URL}/api/documents/`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      })
      if (res.ok) {
        const data = await res.json()
        setDocuments(data.documents)
      }
    } catch {
      console.error('Failed to load documents')
    }
  }

  async function handleUpload(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Only PDF files supported')
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/api/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail ?? 'Upload failed')
      }

      const data = await res.json()
      toast.success(`${file.name} uploaded! Indexing...`)

      setDocuments(prev => [{
        id: data.document_id,
        filename: file.name,
        status: 'processing',
        chunk_count: 0,
        page_count: 0,
        created_at: new Date().toISOString()
      }, ...prev])

      startPolling(data.document_id, file.name)

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      toast.error(msg)
    } finally {
      setUploading(false)
    }
  }

  function startPolling(docId: string, filename: string) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/documents/`, {
          headers: { 'Authorization': `Bearer ${getToken()}` }
        })
        if (res.ok) {
          const data = await res.json()
          const doc = data.documents.find(
            (d: Document) => d.id === docId
          )
          if (doc?.status === 'indexed') {
            setDocuments(data.documents)
            toast.success(`${filename} ready! ${doc.chunk_count} chunks indexed.`)
            clearInterval(interval)
          } else if (doc?.status === 'failed') {
            setDocuments(data.documents)
            toast.error(`Failed to index ${filename}`)
            clearInterval(interval)
          }
        }
      } catch {
        clearInterval(interval)
      }
    }, 2000)

    pollingRef.current.push(interval)
    setTimeout(() => clearInterval(interval), 120000)
  }

  async function handleDelete(docId: string, filename: string) {
    try {
      const res = await fetch(
        `${API_URL}/api/documents/${docId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }
      )
      if (res.ok) {
        setDocuments(prev => prev.filter(d => d.id !== docId))
        if (selectedDocId === docId) {
          onScopeChange('all')
        }
        toast.success(`${filename} deleted`)
      }
    } catch {
      toast.error('Delete failed')
    }
  }

  function triggerFileInput() {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.pdf'
    input.onchange = e => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) handleUpload(file)
    }
    input.click()
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'indexed': return 'bg-green-400'
      case 'failed': return 'bg-red-400'
      default: return 'bg-yellow-400 animate-pulse'
    }
  }

  function getStatusText(status: string) {
    switch (status) {
      case 'indexed': return 'Ready'
      case 'failed': return 'Failed'
      default: return 'Indexing...'
    }
  }

  const hasIndexedDocs = documents.some(d => d.status === 'indexed')

  return (
    <div className="flex flex-col gap-2">

      {/* Upload area */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => {
          e.preventDefault()
          setDragOver(false)
          const file = e.dataTransfer.files[0]
          if (file) handleUpload(file)
        }}
        onClick={triggerFileInput}
        className={`border-2 border-dashed rounded-xl p-3
          text-center cursor-pointer transition-all
          ${dragOver
            ? 'border-indigo-500 bg-indigo-950/50'
            : 'border-gray-600 hover:border-gray-500 hover:bg-gray-800/30'
          }
          ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <svg xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24" fill="currentColor"
          className="w-5 h-5 text-gray-500 mx-auto mb-1">
          <path fillRule="evenodd" d="M11.47 2.47a.75.75 0 011.06
          0l4.5 4.5a.75.75 0 01-1.06 1.06l-3.22-3.22V16.5a.75.75
          0 01-1.5 0V4.81L8.03 8.03a.75.75 0 01-1.06-1.06l4.5-4.5z
          M3 15.75a.75.75 0 01.75.75v2.25a1.5 1.5 0 001.5
          1.5h13.5a1.5 1.5 0 001.5-1.5V16.5a.75.75 0 011.5
          0v2.25a3 3 0 01-3 3H5.25a3 3 0 01-3-3V16.5a.75.75
          0 01.75-.75z" clipRule="evenodd" />
        </svg>
        <p className="text-xs text-gray-500">
          {uploading
            ? 'Uploading...'
            : dragOver
            ? 'Drop to upload'
            : 'Drop PDF or click'}
        </p>
      </div>

      {/* Document list */}
      {documents.length > 0 && (
        <div className="flex flex-col gap-1">
          {/* All Documents — multi-document LangGraph mode */}
          <div
            className={`flex items-center gap-2 px-2 py-2 rounded-lg
              cursor-pointer transition-colors
              ${isAllDocumentsSelected
                ? 'bg-indigo-900/50 border border-indigo-700'
                : 'hover:bg-gray-800 border border-transparent'
              }
              ${!hasIndexedDocs ? 'opacity-60' : ''}`}
            onClick={() => onScopeChange('all')}
          >
            <span className={`w-2 h-2 rounded-full flex-shrink-0
              ${isAllDocumentsSelected ? 'bg-indigo-400' : 'bg-gray-500'}`}
            />
            <div className="flex-1 min-w-0">
              <p className={`text-xs font-medium truncate
                ${isAllDocumentsSelected ? 'text-indigo-200' : 'text-gray-300'}`}>
                All Documents
              </p>
              <p className="text-xs text-gray-600">
                Search across all uploads
              </p>
            </div>
          </div>

          {documents.map(doc => (
            <div
              key={doc.id}
              className={`group flex items-center gap-2 px-2 py-2
                rounded-lg cursor-pointer transition-colors
                ${selectedDocId === doc.id
                  ? 'bg-indigo-900/50 border border-indigo-700'
                  : 'hover:bg-gray-800 border border-transparent'
                }
                ${doc.status !== 'indexed'
                  ? 'opacity-60 pointer-events-none' : ''}`}
              onClick={() => onScopeChange(doc.id)}
            >
              <span className={`w-2 h-2 rounded-full flex-shrink-0
                ${getStatusColor(doc.status)}`}
                title={getStatusText(doc.status)}
              />

              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-300 truncate">
                  {doc.filename}
                </p>
                {doc.status === 'indexed' && (
                  <p className="text-xs text-gray-600">
                    {doc.page_count}p · {doc.chunk_count} chunks
                  </p>
                )}
                {doc.status === 'processing' && (
                  <p className="text-xs text-yellow-600">
                    Indexing...
                  </p>
                )}
              </div>

              {doc.status !== 'processing' && (
                <button
                  onClick={e => {
                    e.stopPropagation()
                    handleDelete(doc.id, doc.filename)
                  }}
                  className="opacity-0 group-hover:opacity-100
                    text-gray-600 hover:text-red-400
                    transition-all p-0.5"
                  title="Delete document"
                >
                  <svg xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24" fill="currentColor"
                    className="w-3.5 h-3.5">
                    <path fillRule="evenodd" d="M16.5 4.478v.227a48.816
                    48.816 0 013.878.512.75.75 0 11-.256
                    1.478l-.209-.035-1.005 13.07a3 3 0
                    01-2.991 2.77H8.084a3 3 0
                    01-2.991-2.77L4.087 6.66l-.209.035a.75.75
                    0 01-.256-1.478A48.567 48.567 0 017.5
                    4.705v-.227c0-1.564 1.213-2.9 2.816-2.951a52.662
                    52.662 0 013.369 0c1.603.051 2.815
                    1.387 2.815 2.951zm-6.136-1.452a51.196
                    51.196 0 013.273 0C14.39 3.05 15 3.684
                    15 4.478v.113a49.488 49.488 0
                    00-6 0v-.113c0-.794.609-1.428
                    1.364-1.452zm-.355 5.945a.75.75 0
                    10-1.5.058l.347 9a.75.75 0
                    101.499-.058l-.346-9zm5.48.058a.75.75
                    0 10-1.498-.058l-.347 9a.75.75 0
                    001.5.058l.345-9z" clipRule="evenodd" />
                  </svg>
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Active scope indicator */}
      {documentScope !== 'chat' && (
        <div className="px-2 py-2 bg-indigo-950/50 border
          border-indigo-800/50 rounded-lg">
          <p className="text-xs text-indigo-300 flex items-center gap-1">
            <span>{isAllDocumentsSelected ? '📚' : '📄'}</span>
            <span>
              {isAllDocumentsSelected
                ? 'All Documents mode active'
                : 'Single document mode active'}
            </span>
          </p>
          <button
            onClick={() => onScopeChange('chat')}
            className="text-xs text-indigo-600
              hover:text-indigo-400 mt-0.5 transition-colors"
          >
            Switch to normal chat
          </button>
        </div>
      )}

      {documents.length === 0 && !uploading && (
        <p className="text-xs text-gray-600 text-center py-2">
          Upload a PDF to start chatting with documents
        </p>
      )}
    </div>
  )
}
