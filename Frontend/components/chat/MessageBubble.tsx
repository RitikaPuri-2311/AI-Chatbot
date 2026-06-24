'use client'
import type { Role } from '@/types'

interface Props {
  role: Role
  content: string
}

export default function MessageBubble({ role, content }: Props) {
  const isUser = role === 'user'

  return (
    <div className={`flex gap-3 items-start 
      ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center 
        justify-center text-xs font-semibold shrink-0 mt-1
        ${isUser 
          ? 'bg-indigo-600 text-white' 
          : 'bg-gray-800 text-white'
        }`}>
        {isUser ? 'You' : 'AI'}
      </div>

      {/* Message */}
      <div className={`max-w-[75%] px-4 py-3 rounded-2xl 
        text-sm leading-relaxed
        ${isUser
          ? 'bg-indigo-600 text-white rounded-tr-sm'
          : 'bg-gray-100 text-gray-800 rounded-tl-sm'
        }`}>
        {content}
      </div>
    </div>
  )
}