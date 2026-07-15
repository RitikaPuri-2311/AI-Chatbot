'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { login, saveAuth } from '@/lib/auth'

export default function LoginForm() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [generalError, setGeneralError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError('')
    setPasswordError('')
    setGeneralError('')

    let hasError = false
    if (!email) {
      setEmailError('Email is required')
      hasError = true
    }
    if (!password) {
      setPasswordError('Password is required')
      hasError = true
    }
    if (hasError) return

    try {
      setLoading(true)
      const result = await login(email, password)
      saveAuth(result.accessToken, result.user)
      router.push('/chat')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Something went wrong'
      setGeneralError(message)
    } finally {
      setLoading(false)
    }
  }

  const inputClass = `w-full border border-[var(--color-border-subtle)] rounded-xl
    px-4 py-2.5 text-sm bg-[var(--color-surface-raised)]
    text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)]
    focus:outline-none focus:ring-2 focus:ring-violet-500/30
    focus:border-violet-500/40 transition-all`

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {generalError && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400
          text-sm px-4 py-3 rounded-xl">
          {generalError}
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-[var(--color-text-secondary)]">
          Email
        </label>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          className={inputClass}
          placeholder="you@example.com"
        />
        {emailError && (
          <span className="text-red-400 text-xs">{emailError}</span>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-[var(--color-text-secondary)]">
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          className={inputClass}
          placeholder="••••••••"
        />
        {passwordError && (
          <span className="text-red-400 text-xs">{passwordError}</span>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-gradient-to-r from-violet-600 to-indigo-600
          text-white py-2.5 rounded-xl text-sm font-medium
          hover:from-violet-500 hover:to-indigo-500
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all shadow-sm shadow-violet-900/20
          flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Logging in...
          </>
        ) : (
          'Sign in'
        )}
      </button>
    </form>
  )
}
