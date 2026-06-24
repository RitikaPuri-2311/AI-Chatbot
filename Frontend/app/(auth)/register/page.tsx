import RegisterForm from '@/components/auth/RegisterForm'
import Link from 'next/link'

export default function RegisterPage() {
  return (
    <main className="min-h-screen flex items-center 
    justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white 
      rounded-2xl shadow-sm border border-gray-100">
        <h1 className="text-2xl font-semibold text-gray-800 mb-2">
          Create account
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          Join to start chatting with AI
        </p>
        <RegisterForm />
        <p className="text-sm text-center text-gray-500 mt-6">
          Already have an account?{' '}
          <Link href="/login"
            className="text-indigo-600 hover:underline font-medium">
            Login
          </Link>
        </p>
      </div>
    </main>
  )
}