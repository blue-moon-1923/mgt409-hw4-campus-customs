import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { formatPrice } from '../api'
import { SUGGESTIONS, useChat } from '../chat'
import BrandMark from './BrandMark'

/**
 * Floating shop assistant.
 *
 * Presentation only — the transcript, the request, and the page results all live
 * in `ChatProvider`, because a reply now updates the page as well as this panel.
 */
export default function ChatWidget() {
  const { messages, isSending, isOpen, setIsOpen, hasUnread, send } = useChat()
  const [draft, setDraft] = useState('')
  const logRef = useRef<HTMLOListElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isSending])

  // Opening the panel should put the cursor where the customer is about to type.
  useEffect(() => {
    if (isOpen) inputRef.current?.focus()
  }, [isOpen])

  // Escape closes, the way every other overlay on the web behaves.
  useEffect(() => {
    if (!isOpen) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isOpen, setIsOpen])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || isSending) return
    setDraft('')
    await send(text)
  }

  const showSuggestions = messages.length === 1 && !isSending

  return (
    <div className="chat-dock">
      {isOpen && (
        <section className="chat-panel" aria-label="Shop assistant">
          <header className="chat-header">
            <div className="chat-identity">
              <BrandMark className="chat-avatar" />
              <div>
                <strong>Shop assistant</strong>
                <span className="chat-status">Answers from our catalogue</span>
              </div>
            </div>
            <button
              type="button"
              className="chat-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close the shop assistant"
            >
              ×
            </button>
          </header>

          <ol className="chat-log" ref={logRef}>
            {messages.map((message, index) => (
              <li key={index} className={`chat-bubble chat-bubble-${message.role}`}>
                <p className="chat-text">{message.content}</p>
                {message.products && message.products.length > 0 && (
                  <>
                    <ul className="chat-products">
                      {message.products.slice(0, 3).map((product) => (
                        <li key={product.product_id}>
                          <Link
                            className="chat-product"
                            to={`/products/${product.product_id}`}
                            onClick={() => setIsOpen(false)}
                          >
                            <img src={product.image_url} alt={product.name} loading="lazy" />
                            <span className="chat-product-words">
                              <strong>{product.name}</strong>
                              <span className="chat-product-price">
                                {formatPrice(product.price)}
                                {!product.in_stock && ' · sold out'}
                              </span>
                            </span>
                          </Link>
                        </li>
                      ))}
                    </ul>
                    <p className="chat-note">
                      {message.products.length === 1
                        ? 'Shown on the page behind this panel.'
                        : `All ${message.products.length} are on the page behind this panel.`}
                    </p>
                  </>
                )}
              </li>
            ))}
            {isSending && (
              <li className="chat-bubble chat-bubble-assistant chat-thinking" aria-live="polite">
                Checking the catalogue
                <span className="chat-dots" aria-hidden="true">
                  <i />
                  <i />
                  <i />
                </span>
              </li>
            )}
          </ol>

          {showSuggestions && (
            <div className="chat-suggestions">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="chat-chip"
                  onClick={() => void send(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form className="chat-composer" onSubmit={handleSubmit}>
            <label className="visually-hidden" htmlFor="chat-input">
              Message the shop assistant
            </label>
            <input
              id="chat-input"
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about a product…"
              autoComplete="off"
              disabled={isSending}
            />
            <button type="submit" disabled={!draft.trim() || isSending}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className="chat-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-label={isOpen ? 'Close the shop assistant' : 'Open the shop assistant'}
      >
        {isOpen ? 'Close' : 'Chat with us'}
        {!isOpen && hasUnread && <span className="chat-toggle-dot" aria-hidden="true" />}
      </button>
    </div>
  )
}
