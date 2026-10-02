'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from './store/useStore'

export default function Home() {
  const router = useRouter()
  const { user, fetchUser, isLoading } = useStore()

  useEffect(() => {
    fetchUser()
  }, [])

  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard')
    }
  }, [user, isLoading])

  return (
    <main className="min-h-screen bg-gradient-to-b from-pink-50 to-white">
      <div className="max-w-4xl mx-auto px-4 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Fashion Creator Agent
          </h1>
          <p className="text-xl text-gray-600 mb-10">
            Create stunning Instagram posts with AI-powered captions and styling suggestions
          </p>

          <div className="flex gap-4 justify-center">
            <button
              onClick={() => router.push('/register')}
              className="btn-primary text-lg px-8 py-3"
            >
              Get Started
            </button>
            <button
              onClick={() => router.push('/login')}
              className="btn-secondary text-lg px-8 py-3"
            >
              Sign In
            </button>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="card text-center">
            <div className="text-4xl mb-4">📸</div>
            <h3 className="text-lg font-semibold mb-2">Upload Your Outfit</h3>
            <p className="text-gray-600">
              Simply upload your outfit photo and let our AI analyze it
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">✨</div>
            <h3 className="text-lg font-semibold mb-2">Get AI Caption</h3>
            <p className="text-gray-600">
              Receive a ready-to-post caption matching your unique voice
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">🛍️</div>
            <h3 className="text-lg font-semibold mb-2">Shop the Look</h3>
            <p className="text-gray-600">
              Get shoppable matching suggestions with affiliate links
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}