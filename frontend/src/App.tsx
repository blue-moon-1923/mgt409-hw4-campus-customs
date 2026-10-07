import { Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth'
import { ChatProvider } from './chat'
import ChatWidget from './components/ChatWidget'
import Footer from './components/Footer'
import NavBar from './components/NavBar'
import About from './pages/About'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import LogIn from './pages/LogIn'
import ProductDetailPage from './pages/ProductDetail'
import Products from './pages/Products'

export default function App() {
  return (
    <AuthProvider>
      <ChatProvider>
        <div className="app-shell">
          <NavBar />
          <main id="main" className="app-main">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:productId" element={<ProductDetailPage />} />
              <Route path="/about" element={<About />} />
              <Route path="/login" element={<LogIn />} />
              <Route path="/create-account" element={<CreateAccount />} />
              <Route
                path="*"
                element={
                  <section className="page narrow">
                    <h1>Page not found</h1>
                    <p>That rack is empty. Try the products page instead.</p>
                  </section>
                }
              />
            </Routes>
          </main>
          <Footer />
          <ChatWidget />
        </div>
      </ChatProvider>
    </AuthProvider>
  )
}
