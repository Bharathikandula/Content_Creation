'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useStore } from '../../store/useStore'
import toast from 'react-hot-toast'

export default function PostDetail() {
  const router = useRouter()
  const params = useParams()
  const postId = parseInt(params.id as string)

  const {
    user, currentPost, fetchUser, fetchPost, uploadPhoto,
    generateContent, generateScript, createCreatorPage, isLoading,
  } = useStore()

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedDuration, setSelectedDuration] = useState(30)
  const [showPageOptions, setShowPageOptions] = useState(false)
  const [showOnPage, setShowOnPage] = useState(false)

  useEffect(() => {
    fetchUser()
    fetchPost(postId)
  }, [postId])

  useEffect(() => {
    if (!user) router.push('/login')
  }, [user])

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      await uploadPhoto(postId, file)
      toast.success('Photo uploaded!')
      await fetchPost(postId)
    } catch (error: any) {
      toast.error('Failed to upload photo')
    }
  }

  const handleGenerate = async (regenerate = false) => {
    try {
      await generateContent(postId, regenerate)
      toast.success('Content generated!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Generation failed')
    }
  }

  const handleGenerateScript = async () => {
    try {
      await generateScript(postId, selectedDuration)
      toast.success('Script generated!')
    } catch (error: any) {
      toast.error('Script generation failed')
    }
  }

  const handleCreatePage = async () => {
    try {
      const slug = await createCreatorPage(postId, showOnPage)
      toast.success('Creator page created!')
      setShowPageOptions(false)
      await fetchPost(postId)
    } catch (error: any) {
      toast.error('Failed to create page')
    }
  }

  const handleCopyCaption = async () => {
    if (!currentPost?.caption_versions?.length) return
    await navigator.clipboard.writeText(currentPost.caption_versions[0].text)
    toast.success('Caption copied!')
  }

  if (!currentPost) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <button onClick={() => router.push('/dashboard')} className="text-primary-600 hover:underline">
            ← Back to Dashboard
          </button>
          <h1 className="text-xl font-bold">Post #{currentPost.id}</h1>
          <div></div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Photo Upload Section */}
        <div className="card mb-6">
          <h2 className="text-xl font-bold mb-4">Outfit Photo</h2>
          {currentPost.photos.length > 0 ? (
            <p className="text-green-600 mb-2">✓ {currentPost.photos.length} photo(s) uploaded</p>
          ) : (
            <p className="text-gray-600 mb-4">Upload your outfit photo to get started</p>
          )}
          <input type="file" ref={fileInputRef} onChange={handlePhotoUpload} accept="image/*" className="hidden" />
          <button onClick={() => fileInputRef.current?.click()} className="btn-secondary">
            {currentPost.photos.length > 0 ? 'Add Another Photo' : 'Upload Photo'}
          </button>
        </div>

        {/* Generate Button */}
        {currentPost.photos.length > 0 && currentPost.status === 'draft' && (
          <div className="card mb-6 text-center">
            <button onClick={() => handleGenerate(false)} disabled={isLoading} className="btn-primary text-lg px-8 py-3">
              {isLoading ? 'Generating...' : '✨ Generate Content'}
            </button>
          </div>
        )}

        {/* Caption Section */}
        {currentPost.caption_versions.length > 0 && (
          <div className="card mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Caption</h2>
              <div className="flex gap-2">
                <button onClick={handleCopyCaption} className="btn-secondary text-sm">Copy</button>
                <button onClick={() => handleGenerate(true)} disabled={isLoading} className="btn-secondary text-sm">Regenerate</button>
              </div>
            </div>
            <p className="text-gray-800 whitespace-pre-wrap">{currentPost.caption_versions[0].text}</p>

            {currentPost.caption_versions[0].hashtags?.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600 mb-2">Hashtags:</p>
                <div className="flex flex-wrap gap-2">
                  {currentPost.caption_versions[0].hashtags.map((tag: string, i: number) => (
                    <span key={i} className="bg-primary-50 text-primary-700 px-2 py-1 rounded-full text-sm">#{tag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Outfit Description */}
        {currentPost.caption_versions[0]?.outfit_description && (
          <div className="card mb-6">
            <h2 className="text-xl font-bold mb-4">Outfit Description</h2>
            <p className="text-gray-800">{currentPost.caption_versions[0].outfit_description}</p>
            {currentPost.caption_versions[0].alt_text && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">Alt Text:</p>
                <p className="text-gray-700 italic">{currentPost.caption_versions[0].alt_text}</p>
              </div>
            )}
          </div>
        )}

        {/* Matching Suggestions */}
        {currentPost.products.length > 0 && (
          <div className="card mb-6">
            <h2 className="text-xl font-bold mb-4">Matching Suggestions</h2>
            <div className="space-y-4">
              {currentPost.products.map((pp: any) => (
                <div key={pp.id} className="flex gap-4 p-4 bg-gray-50 rounded-lg">
                  {pp.product?.image_url && (
                    <img src={pp.product.image_url} alt={pp.product.title} className="w-20 h-20 object-cover rounded" />
                  )}
                  <div className="flex-1">
                    <p className="font-medium">{pp.product?.title || 'Generic Idea'}</p>
                    {pp.product?.price && <p className="text-gray-600">{pp.product.price}</p>}
                    {pp.is_generic_idea && <p className="text-gray-600">{pp.generic_idea_text}</p>}
                    {pp.affiliate_url && (
                      <a href={pp.affiliate_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline text-sm">
                        Shop Now →
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Script Section */}
        <div className="card mb-6">
          <h2 className="text-xl font-bold mb-4">Voiceover Script</h2>
          {currentPost.script ? (
            <div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-gray-600">Duration: {currentPost.script.duration_seconds}s</span>
                <span className="text-gray-600">Words: {currentPost.script.word_count}</span>
              </div>
              <p className="text-gray-800 whitespace-pre-wrap">{currentPost.script.text}</p>
              {currentPost.script.disclosure && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-600">Disclosure:</p>
                  <p className="text-gray-700 italic">{currentPost.script.disclosure}</p>
                </div>
              )}
            </div>
          ) : (
            <div>
              <p className="text-gray-600 mb-4">Generate a voiceover script for your video</p>
              <div className="flex gap-4 items-center">
                <select value={selectedDuration} onChange={(e) => setSelectedDuration(parseInt(e.target.value))} className="input-field w-auto">
                  <option value={15}>15 seconds</option>
                  <option value={30}>30 seconds</option>
                  <option value={45}>45 seconds</option>
                </select>
                <button onClick={handleGenerateScript} disabled={isLoading} className="btn-primary">Generate Script</button>
              </div>
            </div>
          )}
        </div>

        {/* Creator Page Section */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Creator Page</h2>
          {currentPost.creator_page ? (
            <div>
              <p className="text-green-600 mb-2">✓ Page created</p>
              <p className="text-gray-600">Your page is live at: /shop/{currentPost.creator_page.slug}</p>
            </div>
          ) : (
            <div>
              <p className="text-gray-600 mb-4">Create a public page to share your outfit with shoppable links</p>
              {showPageOptions ? (
                <div className="space-y-4">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" checked={showOnPage} onChange={(e) => setShowOnPage(e.target.checked)} className="rounded" />
                    <span className="text-sm text-gray-700">Show outfit photo on page (photo will be kept as long as page is live)</span>
                  </label>
                  <div className="flex gap-2">
                    <button onClick={handleCreatePage} className="btn-primary">Create Page</button>
                    <button onClick={() => setShowPageOptions(false)} className="btn-secondary">Cancel</button>
                  </div>
                </div>
              ) : (
                <button onClick={() => setShowPageOptions(true)} className="btn-primary">Create Creator Page</button>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}