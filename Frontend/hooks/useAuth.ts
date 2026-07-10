'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getToken, getUser } from '@/lib/auth'
import type { User } from '@/types'

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const token = getToken()
    const savedUser = getUser()
    if (!token || !savedUser) {
      router.replace('/login')
    } else {
      setTimeout(() => {
        setUser(savedUser)
      }, 0)
    }
    setTimeout(() => {
      setLoading(false)
    }, 0)
  }, [router])

  return { user, loading }
}