import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth'
import type { SignupFields } from '../types'

const EMPTY: SignupFields = {
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  confirm_password: '',
}

const MIN_PASSWORD_LENGTH = 8

export default function CreateAccount() {
  const { user, signUp, logOut } = useAuth()
  const navigate = useNavigate()
  const [fields, setFields] = useState<SignupFields>(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (user) {
    return (
      <section className="page narrow">
        <p className="eyebrow">Signed in</p>
        <h1>You already have an account</h1>
        <p className="lede">Signed in as {user.first_name ?? user.email}.</p>
        <button className="button button-primary" type="button" onClick={() => void logOut()}>
          Log out
        </button>
      </section>
    )
  }

  const update = (key: keyof SignupFields) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setFields((current) => ({ ...current, [key]: event.target.value }))

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)

    // Checked here for a fast, friendly message; the backend enforces the same
    // two rules again, because a browser check is not a security control.
    if (fields.password !== fields.confirm_password) {
      setError('The two passwords do not match.')
      return
    }
    if (fields.password.length < MIN_PASSWORD_LENGTH) {
      setError(`Please use a password of at least ${MIN_PASSWORD_LENGTH} characters.`)
      return
    }

    setIsSubmitting(true)
    try {
      await signUp(fields)
      navigate('/')
    } catch (cause) {
      setError((cause as Error).message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="page narrow">
      <p className="eyebrow">New here</p>
      <h1>Create an account</h1>
      <p className="lede">
        One account covers online orders, campus pickup, and the shop assistant.
      </p>

      <form className="form-card" onSubmit={handleSubmit} noValidate>
        {error && (
          <p className="notice notice-error" role="alert">
            {error}
          </p>
        )}

        <div className="form-row">
          <div>
            <label htmlFor="signup-first">First name</label>
            <input
              id="signup-first"
              name="first_name"
              autoComplete="given-name"
              value={fields.first_name}
              onChange={update('first_name')}
              required
            />
          </div>
          <div>
            <label htmlFor="signup-last">Last name</label>
            <input
              id="signup-last"
              name="last_name"
              autoComplete="family-name"
              value={fields.last_name}
              onChange={update('last_name')}
              required
            />
          </div>
        </div>

        <label htmlFor="signup-email">Email address</label>
        <input
          id="signup-email"
          type="email"
          name="email"
          autoComplete="email"
          value={fields.email}
          onChange={update('email')}
          required
        />

        <label htmlFor="signup-password">Password</label>
        <input
          id="signup-password"
          type="password"
          name="password"
          autoComplete="new-password"
          minLength={MIN_PASSWORD_LENGTH}
          value={fields.password}
          onChange={update('password')}
          required
        />

        <label htmlFor="signup-confirm">Confirm password</label>
        <input
          id="signup-confirm"
          type="password"
          name="confirm_password"
          autoComplete="new-password"
          value={fields.confirm_password}
          onChange={update('confirm_password')}
          required
        />

        <button className="button button-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </button>
        <p className="form-note">
          At least {MIN_PASSWORD_LENGTH} characters. We store a salted hash of your password,
          never the password itself.
        </p>
      </form>

      <p>
        Already have one? <Link className="text-link" to="/login">Log in</Link>.
      </p>
    </section>
  )
}
