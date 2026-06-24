import LoginForm from '@/components/auth/LoginForm'
import Link from 'next/link'

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center 
    justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white 
      rounded-2xl shadow-sm border border-gray-100">
        <h1 className="text-2xl font-semibold text-gray-800 mb-2">
          Welcome back
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          Sign in to continue to your chatbot
        </p>
        <LoginForm />
        <p className="text-sm text-center text-gray-500 mt-6">
          Don&apos;t have an account?{' '}
          <Link href="/register"
            className="text-indigo-600 hover:underline font-medium">
            Register
          </Link>
        </p>
      </div>
    </main>
  )
}