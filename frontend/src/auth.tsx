import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { fetchCurrentUser, postLogin, postLogout, postSignup } from './api'
import type { PublicUser, SignupFields } from './types'

/**
 * Who is signed in.
 *
 * The session itself lives in an HttpOnly cookie that this code cannot read —
 * the browser attaches it automatically and only the backend can interpret it.
 * All this context holds is the public profile the API chose to return, so no
 * password or hash is ever in frontend state.
 */
interface AuthValue {
  user: PublicUser | null
  isLoading: boolean
  logIn: (email: string, password: string) => Promise<void>
  signUp: (fields: SignupFields) => Promise<void>
  logOut: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Ask the backend who the cookie belongs to, so a page reload stays signed in.
  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  const logIn = useCallback(async (email: string, password: string) => {
    setUser(await postLogin(email, password))
  }, [])

  const signUp = useCallback(async (fields: SignupFields) => {
    setUser(await postSignup(fields))
  }, [])

  const logOut = useCallback(async () => {
    await postLogout()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, isLoading, logIn, signUp, logOut }),
    [user, isLoading, logIn, signUp, logOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside an AuthProvider.')
  return value
}
