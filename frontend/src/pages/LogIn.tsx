import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth'

export default function LogIn() {
  const { user, logIn, logOut } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (user) {
    return (
      <section className="page narrow">
        <p className="eyebrow">Signed in</p>
        <h1>You are logged in</h1>
        <p className="lede">
          Signed in as {user.first_name ?? user.email}. {user.email}
        </p>
        <button className="button button-primary" type="button" onClick={() => void logOut()}>
          Log out
        </button>
      </section>
    )
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await logIn(email, password)
      navigate('/')
    } catch (cause) {
      setError((cause as Error).message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="page narrow">
      <p className="eyebrow">Returning customer</p>
      <h1>Log in</h1>
      <p className="lede">Sign in to see past orders and pick up where your chat left off.</p>

      <form className="form-card" onSubmit={handleSubmit} noValidate>
        {error && (
          <p className="notice notice-error" role="alert">
            {error}
          </p>
        )}

        <label htmlFor="login-email">Email address</label>
        <input
          id="login-email"
          type="email"
          name="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />

        <label htmlFor="login-password">Password</label>
        <input
          id="login-password"
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        <button className="button button-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in…' : 'Log in'}
        </button>
      </form>

      <p>
        Need an account? <Link className="text-link" to="/create-account">Create one</Link>.
      </p>
    </section>
  )
}
