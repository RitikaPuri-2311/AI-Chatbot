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
      setUser(savedUser)
    }
    setLoading(false)
  }, [router])

  return { user, loading }
}