'use client'
import type { Role } from '@/types'

interface Props {
  role: Role
  content: string
}

export default function MessageBubble({ role, content }: Props) {
  const isUser = role === 'user'

  return (
    <div className={`flex flex-col gap-1 
      ${isUser ? 'items-end' : 'items-start'}`}>
      <span className="text-xs text-gray-400 px-1">
        {isUser ? 'You' : 'AI'}
      </span>
      <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm 
        leading-relaxed ${isUser
          ? 'bg-indigo-600 text-white rounded-tr-sm'
          : 'bg-gray-100 text-gray-800 rounded-tl-sm'
        }`}>
        {content}
      </div>
    </div>
  )
}