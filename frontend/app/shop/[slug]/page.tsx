'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface PageData {
  page: { slug: string; show_photo: boolean }
  creator: { name: string }
  post: { caption: string; outfit_description: string; alt_text: string; hashtags: string[] }
  products: Array<{
    type: string; title?: string; price?: string; image_url?: string;
    affiliate_url?: string; source?: string; text?: string; position: number
  }>
  photo_url: string | null
}

export default function CreatorPage() {
  const params = useParams()
  const slug = params.slug as string
  const [data, setData] = useState<PageData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPage()
  }, [slug])

  const fetchPage = async () => {
    try {
      const response = await axios.get(`${API_URL}/pages/${slug}`)
      setData(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Page not found')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="card text-center">
          <h1 className="text-2xl font-bold mb-4">Page Not Found</h1>
          <p className="text-gray-600">{error || 'This page does not exist'}</p>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">{data.creator.name}</h1>
          <p className="text-gray-600">Shop this look</p>
        </div>

        {data.page.show_photo && data.photo_url && (
          <div className="mb-8">
            <img src={data.photo_url} alt={data.post.alt_text || 'Outfit photo'} className="w-full rounded-lg shadow-md" />
          </div>
        )}

        {data.post.caption && (
          <div className="mb-8">
            <p className="text-gray-800 text-lg leading-relaxed">{data.post.caption}</p>
          </div>
        )}

        {data.post.outfit_description && (
          <div className="mb-8 p-4 bg-gray-50 rounded-lg">
            <h2 className="font-semibold mb-2">Outfit Details</h2>
            <p className="text-gray-700">{data.post.outfit_description}</p>
          </div>
        )}

        {data.products.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold mb-4">Shop the Look</h2>
            <div className="space-y-4">
              {data.products.map((product, i) => (
                <div key={i} className="flex gap-4 p-4 border rounded-lg hover:shadow-md transition-shadow">
                  {product.type === 'product' ? (
                    <>
                      {product.image_url && (
                        <img src={product.image_url} alt={product.title} className="w-24 h-24 object-cover rounded" />
                      )}
                      <div className="flex-1">
                        <h3 className="font-medium">{product.title}</h3>
                        {product.price && <p className="text-gray-600 mt-1">{product.price}</p>}
                        {product.source && <p className="text-sm text-gray-500 mt-1">from {product.source}</p>}
                        {product.affiliate_url && (
                          <a href={product.affiliate_url} target="_blank" rel="noopener noreferrer"
                            className="inline-block mt-2 bg-primary-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-700">
                            Shop Now
                          </a>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="flex-1">
                      <p className="text-gray-600 italic">💡 {product.text}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {data.post.hashtags.length > 0 && (
          <div className="mb-8">
            <div className="flex flex-wrap gap-2">
              {data.post.hashtags.map((tag, i) => (
                <span key={i} className="text-primary-600 text-sm">#{tag}</span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-12 pt-8 border-t text-center text-sm text-gray-500">
          <p>This page contains affiliate links. We may earn a commission if you make a purchase through our links.</p>
        </div>
      </div>
    </main>
  )
}