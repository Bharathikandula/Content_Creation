'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useStore } from '../store/useStore'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const router = useRouter()
  const { user, posts, fetchUser, fetchPosts, createPost, isLoading } = useStore()
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    fetchUser()
    fetchPosts()
  }, [])

  useEffect(() => {
    if (!user && !isLoading) {
      router.push('/login')
    }
  }, [user, isLoading])

  const handleCreatePost = async () => {
    setIsCreating(true)
    try {
      const post = await createPost({
        language: user?.language || 'en',
        tone: 'casual',
      })
      toast.success('Post created! Upload a photo to get started.')
      router.push(`/post/${post.id}`)
    } catch (error: any) {
      toast.error('Failed to create post')
    } finally {
      setIsCreating(false)
    }
  }

  if (!user) return null

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary-600">Fashion Creator</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">Welcome, {user.name}</span>
            <button onClick={() => { useStore.getState().logout(); router.push('/') }} className="btn-secondary text-sm">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Your Posts</h2>
          <button onClick={handleCreatePost} disabled={isCreating} className="btn-primary">
            {isCreating ? 'Creating...' : '+ New Post'}
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading posts...</p>
          </div>
        ) : posts.length === 0 ? (
          <div className="card text-center py-12">
            <div className="text-6xl mb-4">📸</div>
            <h3 className="text-xl font-semibold mb-2">No posts yet</h3>
            <p className="text-gray-600 mb-4">Create your first post to get AI-powered captions and styling suggestions</p>
            <button onClick={handleCreatePost} disabled={isCreating} className="btn-primary">
              Create Your First Post
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.map((post) => (
              <div key={post.id} onClick={() => router.push(`/post/${post.id}`)} className="card cursor-pointer hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-sm text-gray-500">{new Date(post.created_at).toLocaleDateString()}</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${post.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                    {post.status}
                  </span>
                </div>

                <div className="mb-4">
                  <p className="text-sm text-gray-600">Language: {post.language.toUpperCase()}</p>
                  <p className="text-sm text-gray-600">Tone: {post.tone}</p>
                </div>

                {post.caption_versions.length > 0 && (
                  <p className="text-gray-800 line-clamp-3">{post.caption_versions[0].text}</p>
                )}

                {post.products.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm text-gray-600">{post.products.length} matching suggestions</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}