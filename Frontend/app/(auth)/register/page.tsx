import { Sparkles } from 'lucide-react'
import RegisterForm from '@/components/auth/RegisterForm'
import Link from 'next/link'

export default function RegisterPage() {
  return (
    <main className="min-h-screen flex bg-[var(--color-surface)]">
      <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-violet-950
        via-[var(--color-surface)] to-indigo-950 items-center justify-center p-12
        relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(124,58,237,0.15),transparent_50%)]" />
        <div className="relative text-center max-w-md">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600
            to-indigo-600 flex items-center justify-center mx-auto mb-6
            shadow-xl shadow-violet-900/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">
            AI Chatbot
          </h1>
          <p className="text-[var(--color-text-secondary)] mt-3 leading-relaxed">
            Create your account and start chatting with AI, documents, and more.
          </p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 sm:p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600
              to-indigo-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold text-[var(--color-text-primary)]">
              AI Chatbot
            </span>
          </div>

          <h1 className="text-2xl font-semibold text-[var(--color-text-primary)] mb-1">
            Create account
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mb-8">
            Join to start chatting with AI
          </p>

          <RegisterForm />

          <p className="text-sm text-center text-[var(--color-text-muted)] mt-8">
            Already have an account?{' '}
            <Link
              href="/login"
              className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
