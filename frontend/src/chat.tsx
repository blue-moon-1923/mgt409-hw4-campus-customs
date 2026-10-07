import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { fetchChatHistory, postChat } from './api'
import { useAuth } from './auth'
import type { ChatProductCard, ChatTurn, PageContext } from './types'

/**
 * Chat state, lifted out of the widget.
 *
 * The widget is no longer the only thing that reacts to a reply: when the agent
 * returns product matches they also become the results grid on the Products
 * page, so the transcript and the results have to live somewhere both the widget
 * and the page can see.
 */

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: ChatProductCard[]
}

export interface ChatResults {
  heading: string
  query: string
  products: ChatProductCard[]
}

interface ChatValue {
  messages: ChatMessage[]
  isSending: boolean
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  hasUnread: boolean
  results: ChatResults | null
  clearResults: () => void
  send: (text: string) => Promise<void>
}

/** Openers, so a first-time visitor can see what the assistant is for. */
export const SUGGESTIONS = [
  'What hoodies do you sell?',
  'Something navy under $60',
  'Do you have XL crewnecks?',
]

export const GREETING: ChatMessage = {
  role: 'assistant',
  content:
    "Hi! I'm the Campus Customs shop assistant. Ask me what we carry, what it costs, or whether something is in stock in your size.",
}

/** How many prior turns travel back to the server with each message. */
const HISTORY_LIMIT = 8

const ChatContext = createContext<ChatValue | null>(null)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING])
  const [isSending, setIsSending] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [results, setResults] = useState<ChatResults | null>(null)
  const [hasUnread, setHasUnread] = useState(false)
  const isOpenRef = useRef(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()

  useEffect(() => {
    isOpenRef.current = isOpen
  }, [isOpen])

  const clearResults = useCallback(() => setResults(null), [])

  // Opening the panel clears the unread marker on the floating button.
  const openPanel = useCallback((open: boolean) => {
    setIsOpen(open)
    if (open) setHasUnread(false)
  }, [])

  // Signing in restores the saved conversation; signing out clears the panel so
  // one customer's transcript is never left on screen for the next person.
  const signedInUserId = user?.id ?? null
  useEffect(() => {
    if (signedInUserId === null) {
      setMessages([GREETING])
      setResults(null)
      return
    }
    let cancelled = false
    fetchChatHistory()
      .then((history) => {
        if (cancelled) return
        if (history.messages.length === 0) {
          setMessages([GREETING])
          return
        }
        setMessages([
          GREETING,
          ...history.messages.map((stored) => ({
            role: stored.role,
            content: stored.content,
            products: stored.products.length > 0 ? stored.products : undefined,
          })),
        ])
      })
      .catch(() => {
        // A failed restore should not block chatting; start fresh instead.
        if (!cancelled) setMessages([GREETING])
      })
    return () => {
      cancelled = true
    }
  }, [signedInUserId])

  /** Where the customer is standing, so "do you have this in another colour?" resolves. */
  const pageContext = useCallback((): PageContext => {
    const match = location.pathname.match(/^\/products\/(.+)$/)
    return {
      path: location.pathname,
      product_id: match ? decodeURIComponent(match[1]) : null,
      results_heading: results?.heading ?? null,
    }
  }, [location.pathname, results])

  const send = useCallback(
    async (text: string) => {
      const history: ChatTurn[] = messages
        .filter((message) => message !== GREETING)
        .slice(-HISTORY_LIMIT)
        .map(({ role, content }) => ({ role, content }))

      setMessages((current) => [...current, { role: 'user', content: text }])
      setIsSending(true)

      try {
        const answer = await postChat(text, history, pageContext())
        setMessages((current) => [
          ...current,
          { role: 'assistant', content: answer.reply, products: answer.products },
        ])
        setHasUnread((wasUnread) => (isOpenRef.current ? wasUnread : true))

        // Products in the reply become the page's results grid. An answer with no
        // products — a refusal, a greeting — leaves whatever is on screen alone.
        if (answer.products.length > 0) {
          setResults({
            heading: answer.results_heading || 'Matching products',
            query: text,
            products: answer.products,
          })
          navigate('/products')
        }
      } catch (cause) {
        setMessages((current) => [
          ...current,
          { role: 'assistant', content: (cause as Error).message },
        ])
      } finally {
        setIsSending(false)
      }
    },
    [messages, navigate, pageContext],
  )

  const value = useMemo(
    () => ({
      messages,
      isSending,
      isOpen,
      setIsOpen: openPanel,
      hasUnread,
      results,
      clearResults,
      send,
    }),
    [messages, isSending, isOpen, openPanel, hasUnread, results, clearResults, send],
  )

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat(): ChatValue {
  const value = useContext(ChatContext)
  if (!value) throw new Error('useChat must be used inside a ChatProvider.')
  return value
}
