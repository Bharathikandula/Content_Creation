import { create } from 'zustand'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface User {
  id: number
  email: string
  name: string
  language: string
  default_tone: string
}

interface Post {
  id: number
  language: string
  tone: string
  status: string
  created_at: string
  photos: any[]
  caption_versions: any[]
  products: any[]
  creator_page: any
  script: any
}

interface Store {
  user: User | null
  token: string | null
  posts: Post[]
  currentPost: Post | null
  isLoading: boolean

  login: (email: string, password: string) => Promise<void>
  register: (email: string, name: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>

  createPost: (data: { language?: string; tone?: string }) => Promise<Post>
  fetchPosts: () => Promise<void>
  fetchPost: (id: number) => Promise<void>
  uploadPhoto: (postId: number, file: File) => Promise<void>
  generateContent: (postId: number, regenerate?: boolean) => Promise<void>
  generateScript: (postId: number, duration: number) => Promise<void>

  createCreatorPage: (postId: number, showPhoto?: boolean) => Promise<string>
}

export const useStore = create<Store>((set, get) => ({
  user: null,
  token: typeof window !== 'undefined' ? localStorage.getItem('token') : null,
  posts: [],
  currentPost: null,
  isLoading: false,

  login: async (email, password) => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await axios.post(`${API_URL}/auth/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    const { access_token } = response.data
    localStorage.setItem('token', access_token)
    set({ token: access_token })

    await get().fetchUser()
  },

  register: async (email, name, password) => {
    await axios.post(`${API_URL}/auth/register`, { email, name, password })
    await get().login(email, password)
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null, posts: [], currentPost: null })
  },

  fetchUser: async () => {
    const { token } = get()
    if (!token) return

    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      set({ user: response.data })
    } catch (error) {
      get().logout()
    }
  },

  createPost: async (data) => {
    const { token } = get()
    const response = await axios.post(`${API_URL}/posts`, data, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.data
  },

  fetchPosts: async () => {
    const { token } = get()
    if (!token) return

    set({ isLoading: true })
    try {
      const response = await axios.get(`${API_URL}/posts`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      set({ posts: response.data })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchPost: async (id) => {
    const { token } = get()
    if (!token) return

    set({ isLoading: true })
    try {
      const response = await axios.get(`${API_URL}/posts/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      set({ currentPost: response.data })
    } finally {
      set({ isLoading: false })
    }
  },

  uploadPhoto: async (postId, file) => {
    const { token } = get()
    const formData = new FormData()
    formData.append('file', file)

    await axios.post(`${API_URL}/posts/${postId}/photo`, formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  generateContent: async (postId, regenerate = false) => {
    const { token } = get()
    set({ isLoading: true })

    try {
      const response = await axios.post(
        `${API_URL}/posts/${postId}/generate`,
        { post_id: postId, regenerate },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      set({ currentPost: response.data })
    } finally {
      set({ isLoading: false })
    }
  },

  generateScript: async (postId, duration) => {
    const { token } = get()
    set({ isLoading: true })

    try {
      await axios.post(
        `${API_URL}/posts/${postId}/script`,
        { post_id: postId, duration_seconds: duration },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      await get().fetchPost(postId)
    } finally {
      set({ isLoading: false })
    }
  },

  createCreatorPage: async (postId, showPhoto = false) => {
    const { token } = get()
    const response = await axios.post(
      `${API_URL}/pages`,
      { post_id: postId, show_photo: showPhoto },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    return response.data.slug
  },
}))