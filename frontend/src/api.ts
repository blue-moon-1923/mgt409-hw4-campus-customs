import type {
  ChatHistoryResponse,
  ChatResponse,
  ChatTurn,
  PageContext,
  ProductDetail,
  ProductSummary,
  PublicUser,
  SignupFields,
} from './types'

/** Pull a readable message out of a FastAPI error body. */
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
  } catch {
    // fall through to the status-based message
  }
  if (response.status === 404) return 'We could not find that product.'
  return `The storefront API returned ${response.status}. Is the backend running on port 8000?`
}

async function getJSON<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) throw new Error(await errorMessage(response))
  return (await response.json()) as T
}

async function postJSON<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const fetchProducts = () => getJSON<ProductSummary[]>('/api/products')

export const fetchProduct = (productId: string) =>
  getJSON<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`)

/** Up to four other products in the same category, for the "More like this" row. */
export const fetchRelated = (productId: string) =>
  getJSON<ProductSummary[]>(`/api/products/${encodeURIComponent(productId)}/related`)

/** The signed-in account, or null when the session cookie is absent or expired. */
export async function fetchCurrentUser(): Promise<PublicUser | null> {
  const response = await fetch('/api/auth/me')
  if (response.status === 401) return null
  if (!response.ok) throw new Error(await errorMessage(response))
  return (await response.json()) as PublicUser
}

export const postLogin = (email: string, password: string) =>
  postJSON<PublicUser>('/api/auth/login', { email, password })

export const postSignup = (fields: SignupFields) => postJSON<PublicUser>('/api/auth/signup', fields)

export const postLogout = () => postJSON<void>('/api/auth/logout')

export const postChat = (message: string, history: ChatTurn[], page: PageContext) =>
  postJSON<ChatResponse>('/api/chat', { message, history, page })

/** The signed-in customer's saved transcript. Returns an empty list for a guest. */
export const fetchChatHistory = () => getJSON<ChatHistoryResponse>('/api/chat/history')

export const formatPrice = (price: number) =>
  price.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 })
