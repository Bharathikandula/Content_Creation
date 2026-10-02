'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '../store/useStore'
import toast from 'react-hot-toast'

export default function Register() {
  const router = useRouter()
  const { register } = useStore()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [language, setLanguage] = useState('en')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await register(email, name, password)
      toast.success('Account created successfully!')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-pink-50 to-white flex items-center justify-center">
      <div className="card w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8">Create Account</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input-field" required />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" required />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field" required minLength={8} />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} className="input-field">
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="te">Telugu</option>
              <option value="ta">Tamil</option>
              <option value="ml">Malayalam</option>
            </select>
          </div>

          <button type="submit" disabled={isLoading} className="btn-primary w-full">
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center mt-4 text-gray-600">
          Already have an account?{' '}
          <button onClick={() => router.push('/login')} className="text-primary-600 hover:underline">
            Sign In
          </button>
        </p>
      </div>
    </main>
  )
}