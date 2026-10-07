import { NavLink } from 'react-router-dom'

import { useAuth } from '../auth'
import BrandMark from './BrandMark'

const BROWSE_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const GUEST_LINKS = [
  { to: '/login', label: 'Log In' },
  { to: '/create-account', label: 'Create Account' },
]

export default function NavBar() {
  const { user, isLoading, logOut } = useAuth()

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <div className="announce">
        <p className="announce-inner">
          <span>Free campus pickup</span>
          <span className="announce-dot" aria-hidden="true" />
          <span>Printed in New Haven</span>
          <span className="announce-dot" aria-hidden="true" />
          <span>XS–XXL on every design</span>
        </p>
      </div>
      <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="brand" aria-label="Campus Customs home">
          <BrandMark />
          <span className="brand-words">
            <strong>Campus Customs</strong>
            <small>New Haven, Connecticut</small>
          </span>
        </NavLink>
        <nav aria-label="Main">
          <ul className="nav-links">
            {BROWSE_LINKS.map((link) => (
              <li key={link.to}>
                <NavLink
                  to={link.to}
                  end={link.to === '/'}
                  className={({ isActive }) => (isActive ? 'nav-link is-active' : 'nav-link')}
                >
                  {link.label}
                </NavLink>
              </li>
            ))}

            {isLoading ? null : user ? (
              <>
                <li>
                  <span className="nav-greeting">
                    Hi, {user.first_name ?? user.email}
                  </span>
                </li>
                <li>
                  <button type="button" className="nav-link nav-button" onClick={() => void logOut()}>
                    Log Out
                  </button>
                </li>
              </>
            ) : (
              GUEST_LINKS.map((link) => (
                <li key={link.to}>
                  <NavLink
                    to={link.to}
                    className={({ isActive }) => (isActive ? 'nav-link is-active' : 'nav-link')}
                  >
                    {link.label}
                  </NavLink>
                </li>
              ))
            )}
          </ul>
        </nav>
      </div>
      </header>
    </>
  )
}
