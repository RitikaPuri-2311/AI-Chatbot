'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { register, saveAuth } from '@/lib/auth'

export default function RegisterForm() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [generalError, setGeneralError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEmailError('')
    setUsernameError('')
    setPasswordError('')
    setGeneralError('')

    let hasError = false
    if (!email) { setEmailError('Email is required'); hasError = true }
    if (!username) { setUsernameError('Username is required'); hasError = true }
    if (!password) { setPasswordError('Password is required'); hasError = true }
    if (hasError) return

    try {
      setLoading(true)
      const result = await register(email, username, password)
      saveAuth(result.accessToken, result.user)
      router.push('/chat')
    } catch (err: unknown) {
      const message = err instanceof Error
        ? err.message
        : 'Something went wrong'
      setGeneralError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {generalError && (
        <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg">
          {generalError}
        </div>
      )}

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">Email</label>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 
          text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="you@example.com"
        />
        {emailError && (
          <span className="text-red-500 text-xs">{emailError}</span>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">Username</label>
        <input
          type="text"
          value={username}
          onChange={e => setUsername(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 
          text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="yourname"
        />
        {usernameError && (
          <span className="text-red-500 text-xs">{usernameError}</span>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">Password</label>
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 
          text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="••••••••"
        />
        {passwordError && (
          <span className="text-red-500 text-xs">{passwordError}</span>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="bg-indigo-600 text-white py-2 rounded-lg text-sm 
        font-medium hover:bg-indigo-700 disabled:opacity-50 
        disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Creating account...' : 'Register'}
      </button>
    </form>
  )
}